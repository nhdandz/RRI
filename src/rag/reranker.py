"""Cross-encoder Reranker for improving retrieval quality."""

from src.core.logging import get_logger
from src.rag.retriever import RetrievedDocument

logger = get_logger(__name__)


class CrossEncoderReranker:
    """Reranks retrieved documents using cross-encoder scoring."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    async def rerank(
        self,
        query: str,
        documents: list[RetrievedDocument],
        top_k: int = 5,
    ) -> list[RetrievedDocument]:
        if not documents:
            return []

        pairs = [(query, doc.content[:512]) for doc in documents]
        scores = self.model.predict(pairs)

        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        result = []
        for doc, score in scored_docs[:top_k]:
            doc.score = float(score)
            result.append(doc)

        return result
