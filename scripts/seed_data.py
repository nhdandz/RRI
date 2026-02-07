"""Seed database with sample data for development."""

import asyncio
from datetime import date, datetime

from src.storage.database import async_session_factory, init_db
from src.storage.models.paper import Paper
from src.storage.models.repository import Repository


async def seed():
    await init_db()

    async with async_session_factory() as session:
        # Seed sample papers
        papers = [
            Paper(
                arxiv_id="2401.12345",
                title="Attention Is All You Need (v2)",
                abstract="We propose a new attention mechanism for transformer architectures...",
                authors=[{"name": "John Doe", "affiliation": "MIT"}],
                categories=["cs.AI", "cs.CL"],
                published_date=date(2024, 1, 15),
                source="arxiv",
                source_url="https://arxiv.org/abs/2401.12345",
                citation_count=150,
            ),
            Paper(
                arxiv_id="2401.67890",
                title="RAG: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                abstract="Large pre-trained language models store factual knowledge...",
                authors=[{"name": "Jane Smith", "affiliation": "Google"}],
                categories=["cs.CL", "cs.IR"],
                published_date=date(2024, 1, 20),
                source="arxiv",
                source_url="https://arxiv.org/abs/2401.67890",
                citation_count=85,
            ),
        ]

        repos = [
            Repository(
                github_id=1001,
                full_name="langchain-ai/langchain",
                name="langchain",
                owner="langchain-ai",
                description="Building applications with LLMs through composability",
                html_url="https://github.com/langchain-ai/langchain",
                primary_language="Python",
                topics=["llm", "rag", "ai"],
                stars_count=75000,
                forks_count=12000,
                has_readme=True,
                has_license=True,
            ),
            Repository(
                github_id=1002,
                full_name="vllm-project/vllm",
                name="vllm",
                owner="vllm-project",
                description="A high-throughput and memory-efficient inference engine for LLMs",
                html_url="https://github.com/vllm-project/vllm",
                primary_language="Python",
                topics=["llm", "inference", "gpu"],
                stars_count=30000,
                forks_count=4000,
                has_readme=True,
                has_license=True,
            ),
        ]

        for p in papers:
            session.add(p)
        for r in repos:
            session.add(r)

        await session.commit()
        print(f"Seeded {len(papers)} papers and {len(repos)} repositories")


if __name__ == "__main__":
    asyncio.run(seed())
