"""Full RAG Pipeline for research Q&A with multilingual support."""

from dataclasses import dataclass

from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.rag.generator import AnswerGenerator
from src.rag.reranker import CrossEncoderReranker
from src.rag.retriever import HybridRetriever

logger = get_logger(__name__)

TRANSLATE_PROMPT = """Translate the following text to English.
Return ONLY the English translation, nothing else.

Text: {text}

English translation:"""


def _is_english(text: str) -> bool:
    """Check if text is likely English by ASCII letter ratio."""
    if not text:
        return True
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    total_letters = sum(1 for c in text if c.isalpha())
    if total_letters == 0:
        return True
    return (ascii_letters / total_letters) > 0.8


@dataclass
class RAGResponse:
    answer: str
    sources: list[dict]
    confidence: float


class RAGPipeline:
    """
    Full RAG pipeline for research Q&A.

    Flow:
    1. Detect language → translate to English if needed
    2. Hybrid Retrieval (BM25 + Vector)
    3. Reranking (Cross-encoder)
    4. Answer Generation (in user's original language)
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        generator: AnswerGenerator,
        llm_client: BaseLLMClient | None = None,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.generator = generator
        self.llm = llm_client

    async def _translate_to_english(self, text: str) -> str:
        """Translate non-English text to English using LLM."""
        if not self.llm:
            logger.warning("No LLM client for translation, using original query")
            return text
        try:
            prompt = TRANSLATE_PROMPT.format(text=text)
            translated = await self.llm.generate(
                prompt, max_tokens=200, temperature=0.1
            )
            translated = translated.strip()
            logger.info(
                "Translated query",
                original=text[:80],
                translated=translated[:80],
            )
            return translated
        except Exception as e:
            logger.warning("Translation failed, using original query", error=str(e))
            return text

    async def query(
        self,
        question: str,
        top_k: int = 10,
        rerank_top_k: int = 5,
        filters: dict | None = None,
    ) -> RAGResponse:
        # 0. Translate non-English queries for better embedding match
        search_query = question
        if not _is_english(question):
            search_query = await self._translate_to_english(question)

        # 1. Retrieve relevant documents (using English query)
        retrieved = await self.retriever.retrieve(
            query=search_query, top_k=top_k, filters=filters
        )

        if not retrieved:
            # Fallback: answer using LLM general knowledge when no context found
            fallback_answer = await self.generator.generate_fallback(query=question)
            return RAGResponse(
                answer=fallback_answer,
                sources=[],
                confidence=0.0,
            )

        # 2. Rerank for relevance
        reranked = await self.reranker.rerank(
            query=search_query, documents=retrieved, top_k=rerank_top_k
        )

        # 3. Generate answer with citations (use original question for natural response)
        answer, citations = await self.generator.generate(
            query=question, context=reranked
        )

        # 4. Build response
        sources = [
            {
                "id": doc.id,
                "type": doc.source_type,
                "title": doc.title,
                "url": doc.url,
                "relevance_score": doc.score,
            }
            for doc in reranked
        ]

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=self._calculate_confidence(reranked),
        )

    def _calculate_confidence(self, documents: list) -> float:
        if not documents:
            return 0.0
        top_scores = [d.score for d in documents[:3]]
        return sum(top_scores) / len(top_scores)
