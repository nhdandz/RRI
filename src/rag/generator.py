"""Answer Generator with citations for RAG pipeline."""

import re

from src.core.logging import get_logger
from src.llm.base import BaseLLMClient
from src.rag.retriever import RetrievedDocument

logger = get_logger(__name__)

GENERATION_PROMPT = """
You are a research assistant. Answer the question based on the provided context.

Rules:
1. Only use information from the provided context
2. Cite sources using [1], [2], etc.
3. If you're not sure, say so
4. Be concise but thorough

Context:
{context}

Question: {question}

Answer:
"""

FALLBACK_PROMPT = """
You are a research assistant specializing in AI, machine learning, and software engineering.
Answer the following question using your general knowledge.

Note: This answer is based on general knowledge, not from the research database.
Be concise but thorough.

Question: {question}

Answer:
"""


class AnswerGenerator:
    """Generates answers with citations from retrieved context."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client

    async def generate(
        self,
        query: str,
        context: list[RetrievedDocument],
    ) -> tuple[str, list[dict]]:
        context_str = self._format_context(context)

        prompt = GENERATION_PROMPT.format(context=context_str, question=query)

        response = await self.llm.generate(
            prompt, max_tokens=1000, temperature=0.3
        )

        citations = self._extract_citations(response, context)
        return response, citations

    def _format_context(self, documents: list[RetrievedDocument]) -> str:
        parts = []
        for i, doc in enumerate(documents, 1):
            parts.append(f"[{i}] {doc.title}\n{doc.content[:500]}")
        return "\n\n".join(parts)

    async def generate_fallback(self, query: str) -> str:
        prompt = FALLBACK_PROMPT.format(question=query)
        return await self.llm.generate(prompt, max_tokens=1000, temperature=0.7)

    def _extract_citations(
        self, answer: str, documents: list[RetrievedDocument]
    ) -> list[dict]:
        citation_pattern = re.compile(r"\[(\d+)\]")
        cited_indices = set(int(m) for m in citation_pattern.findall(answer))

        citations = []
        for idx in sorted(cited_indices):
            if 1 <= idx <= len(documents):
                doc = documents[idx - 1]
                citations.append(
                    {
                        "index": idx,
                        "document_id": doc.id,
                        "title": doc.title,
                        "url": doc.url,
                    }
                )
        return citations
