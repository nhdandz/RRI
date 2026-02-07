"""Hybrid Retriever combining BM25 and vector search."""

from dataclasses import dataclass

from src.core.logging import get_logger
from src.processors.embedding import EmbeddingGenerator
from src.storage.vector.qdrant_client import VectorStore

logger = get_logger(__name__)


@dataclass
class RetrievedDocument:
    id: str
    source_type: str
    title: str
    content: str
    url: str | None
    score: float


class HybridRetriever:
    """Hybrid retrieval combining BM25 and vector search."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingGenerator,
    ):
        self.vector_store = vector_store
        self.embeddings = embedding_model

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
        collections: list[str] | None = None,
    ) -> list[RetrievedDocument]:
        query_embedding = self.embeddings.embed(query)
        target_collections = collections or ["papers", "repositories", "chunks"]

        all_results = []
        for collection in target_collections:
            results = self.vector_store.search(
                collection=collection,
                query_vector=query_embedding,
                limit=top_k,
                filters=filters,
            )
            for hit in results:
                payload = hit.get("payload", {})
                all_results.append(
                    RetrievedDocument(
                        id=str(hit["id"]),
                        source_type=payload.get("source_type", collection),
                        title=payload.get("title", ""),
                        content=payload.get("content", payload.get("abstract", "")),
                        url=payload.get("url"),
                        score=hit["score"],
                    )
                )

        # Sort by score descending
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:top_k]
