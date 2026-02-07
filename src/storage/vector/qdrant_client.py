from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

COLLECTIONS_CONFIG = {
    "papers": {
        "size": 768,
        "distance": Distance.COSINE,
    },
    "repositories": {
        "size": 768,
        "distance": Distance.COSINE,
    },
    "chunks": {
        "size": 768,
        "distance": Distance.COSINE,
    },
    "user_docs": {
        "size": 768,
        "distance": Distance.COSINE,
    },
}


class VectorStore:
    def __init__(self):
        settings = get_settings()
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

    def init_collections(self) -> None:
        for name, config in COLLECTIONS_CONFIG.items():
            existing = self.client.get_collections().collections
            existing_names = [c.name for c in existing]

            if name not in existing_names:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=config["size"],
                        distance=config["distance"],
                    ),
                )
                logger.info("Created Qdrant collection", collection=name)

    def upsert(
        self,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict,
    ) -> None:
        self.client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def upsert_batch(
        self,
        collection: str,
        points: list[dict],
    ) -> None:
        """Upsert multiple points at once. Each dict: {id, vector, payload}."""
        self.client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"],
                )
                for p in points
            ],
        )

    def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            query_filter = Filter(must=conditions)

        results = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results.points
        ]

    def delete(self, collection: str, point_ids: list[str]) -> None:
        self.client.delete(
            collection_name=collection,
            points_selector=point_ids,
        )
