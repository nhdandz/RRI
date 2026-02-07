"""Index ALL existing data from PostgreSQL into Qdrant.

Embed-only pipeline: no LLM required (no classify/summarize).
Uses metadata already present in DB (categories, topics, keywords).
Batch embedding for much better performance.

Run inside Docker:  docker compose exec worker python -m scripts.index_all
Run on host (GPU):  DATABASE_URL=postgresql+asyncpg://osint:password@localhost:5432/osint \
                    QDRANT_URL=http://localhost:6333 \
                    python -m scripts.index_all
"""

import asyncio
import os

# When running outside Docker, override hostnames to localhost
if os.environ.get("RUN_LOCAL"):
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://osint:password@localhost:5432/osint")
    os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

from src.core.logging import get_logger, setup_logging
from src.processors.embedding import EmbeddingGenerator
from src.storage.database import create_async_session_factory
from src.storage.repositories.github_repo import GitHubRepository
from src.storage.repositories.paper_repo import PaperRepository
from src.storage.vector.qdrant_client import VectorStore

logger = get_logger(__name__)
BATCH_SIZE = 50


async def index_all_papers():
    async_session_factory = create_async_session_factory()
    embedding_gen = EmbeddingGenerator()
    vector_store = VectorStore()
    vector_store.init_collections()

    total = 0
    while True:
        async with async_session_factory() as session:
            repo = PaperRepository(session)
            papers = await repo.get_unprocessed(limit=BATCH_SIZE)

            if not papers:
                break

            # Prepare texts for batch embedding
            texts = [
                f"{paper.title}\n\n{paper.abstract or ''}"
                for paper in papers
            ]

            # Batch embed all at once
            embeddings = embedding_gen.embed_batch(texts)

            # Prepare batch upsert
            points = []
            for paper, embedding in zip(papers, embeddings):
                try:
                    points.append({
                        "id": str(paper.id),
                        "vector": embedding,
                        "payload": {
                            "arxiv_id": paper.arxiv_id,
                            "title": paper.title,
                            "abstract": (paper.abstract or "")[:500],
                            "categories": paper.categories or [],
                            "topics": paper.topics or [],
                            "keywords": paper.keywords or [],
                            "published_date": str(paper.published_date) if paper.published_date else None,
                            "citation_count": paper.citation_count,
                            "source_type": "paper",
                            "url": paper.source_url,
                        },
                    })
                    paper.is_processed = True
                    total += 1
                except Exception as e:
                    logger.error("Failed to prepare paper", arxiv_id=paper.arxiv_id, error=str(e))

            # Batch upsert to Qdrant
            if points:
                vector_store.upsert_batch(collection="papers", points=points)

            await session.commit()
            logger.info("Indexed papers batch", batch=len(points), total=total)

    print(f"Indexed {total} papers into Qdrant")
    return total


async def index_all_repos():
    async_session_factory = create_async_session_factory()
    embedding_gen = EmbeddingGenerator()
    vector_store = VectorStore()
    vector_store.init_collections()

    total = 0
    while True:
        async with async_session_factory() as session:
            repo_store = GitHubRepository(session)
            repos = await repo_store.get_unprocessed(limit=BATCH_SIZE)

            if not repos:
                break

            # Prepare texts for batch embedding
            texts = []
            for r in repos:
                parts = [r.name, r.description or ""]
                if r.readme_content:
                    parts.append(r.readme_content[:2000])
                texts.append("\n\n".join(parts))

            # Batch embed all at once
            embeddings = embedding_gen.embed_batch(texts)

            # Prepare batch upsert
            points = []
            for repository, embedding in zip(repos, embeddings):
                try:
                    points.append({
                        "id": str(repository.id),
                        "vector": embedding,
                        "payload": {
                            "full_name": repository.full_name,
                            "title": repository.name,
                            "description": repository.description or "",
                            "content": repository.description or "",
                            "primary_language": repository.primary_language,
                            "topics": repository.topics or [],
                            "frameworks": repository.frameworks or [],
                            "stars_count": repository.stars_count,
                            "source_type": "repository",
                            "url": repository.html_url,
                        },
                    })
                    repository.is_processed = True
                    total += 1
                except Exception as e:
                    logger.error("Failed to prepare repo", name=repository.full_name, error=str(e))

            # Batch upsert to Qdrant
            if points:
                vector_store.upsert_batch(collection="repositories", points=points)

            await session.commit()
            logger.info("Indexed repos batch", batch=len(points), total=total)

    print(f"Indexed {total} repositories into Qdrant")
    return total


async def main():
    setup_logging()
    print("=" * 60)
    print("Indexing ALL existing data into Qdrant (embed-only, batch)...")
    print("=" * 60)

    papers_count = await index_all_papers()
    repos_count = await index_all_repos()

    print("=" * 60)
    print(f"Done! Indexed {papers_count} papers + {repos_count} repos")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
