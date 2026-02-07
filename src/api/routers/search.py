import asyncio
from functools import partial

from fastapi import APIRouter, Query

from src.api.schemas.search import SearchResponse, SearchResult
from src.processors.embedding import EmbeddingGenerator
from src.storage.vector.qdrant_client import VectorStore

router = APIRouter(prefix="/search", tags=["Search"])

_embedding_gen = EmbeddingGenerator()


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2),
    type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    vector_store = VectorStore()

    # Run CPU-heavy embedding in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    query_embedding = await loop.run_in_executor(None, partial(_embedding_gen.embed, q))

    type_to_collection = {"paper": "papers", "repository": "repositories"}
    if type and type != "all":
        collections = [type_to_collection.get(type, type)]
    else:
        collections = ["papers", "repositories"]

    results = []
    for collection in collections:
        hits = vector_store.search(
            collection=collection,
            query_vector=query_embedding,
            limit=limit,
        )
        for hit in hits:
            payload = hit.get("payload", {})
            results.append(
                SearchResult(
                    id=str(hit["id"]),
                    type=collection.rstrip("s"),
                    title=payload.get("title", ""),
                    description=payload.get("description", payload.get("abstract", "")),
                    url=payload.get("url"),
                    score=hit["score"],
                    metadata=payload,
                )
            )

    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:limit]

    return SearchResponse(query=q, results=results, total=len(results))
