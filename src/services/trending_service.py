"""Trending business logic service."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.repositories.metrics_repo import MetricsRepository


class TrendingService:
    def __init__(self, session: AsyncSession):
        self.metrics = MetricsRepository(session)

    async def get_trending_papers(
        self, period: str = "week", category: str | None = None, limit: int = 20
    ):
        return await self.metrics.get_trending(
            entity_type="paper", category=category, limit=limit
        )

    async def get_trending_repos(
        self,
        period: str = "week",
        language: str | None = None,
        topic: str | None = None,
        limit: int = 20,
    ):
        return await self.metrics.get_trending(
            entity_type="repository", category=topic, limit=limit
        )
