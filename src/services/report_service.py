"""Report generation service."""

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.repositories.metrics_repo import MetricsRepository
from src.storage.repositories.paper_repo import PaperRepository


class ReportService:
    def __init__(self, session: AsyncSession):
        self.paper_repo = PaperRepository(session)
        self.metrics_repo = MetricsRepository(session)

    async def get_weekly_report(
        self, week: date | None = None, topics: list[str] | None = None
    ) -> dict:
        period_end = week or date.today()
        period_start = period_end - timedelta(days=7)

        papers, total = await self.paper_repo.list_papers(
            date_from=period_start,
            date_to=period_end,
            limit=100,
        )

        trending = await self.metrics_repo.get_trending(limit=10)

        return {
            "period_start": period_start,
            "period_end": period_end,
            "new_papers_count": total,
            "new_repos_count": 0,
            "highlights": [],
            "trending_topics": [],
            "report_content": f"Weekly report for {period_start} - {period_end}",
        }
