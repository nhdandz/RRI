"""
Papers With Code API Client

API Docs: https://paperswithcode.com/api/v1
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PWCPaper:
    paper_id: str
    arxiv_id: str | None
    title: str
    abstract: str | None
    url_abs: str | None
    url_pdf: str | None
    repositories: list[dict]


class PapersWithCodeCollector(BaseCollector):
    """Collects paper-code links from Papers With Code."""

    BASE_URL = "https://paperswithcode.com/api/v1"

    def __init__(self):
        super().__init__(
            CollectorConfig(
                name="papers_with_code",
                base_url=self.BASE_URL,
                rate_limit_per_minute=30,
            )
        )

    def _get_headers(self) -> dict:
        return {"Accept": "application/json"}

    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult[PWCPaper]]:
        async for result in self.search_papers(**kwargs):
            yield result

    async def search_papers(
        self,
        query: str = "",
        max_results: int = 50,
    ) -> AsyncIterator[CollectorResult[PWCPaper]]:
        page = 1
        collected = 0

        while collected < max_results:
            params = {"q": query, "page": page, "items_per_page": 50}
            response = await self._request(
                "GET", f"{self.BASE_URL}/papers/", params=params
            )
            data = response.json()
            results = data.get("results", [])

            if not results:
                break

            for item in results:
                yield CollectorResult(
                    data=PWCPaper(
                        paper_id=item.get("id", ""),
                        arxiv_id=item.get("arxiv_id"),
                        title=item.get("title", ""),
                        abstract=item.get("abstract"),
                        url_abs=item.get("url_abs"),
                        url_pdf=item.get("url_pdf"),
                        repositories=item.get("repositories", []),
                    ),
                    source="papers_with_code",
                    collected_at=datetime.utcnow(),
                )
                collected += 1

            if not data.get("next"):
                break
            page += 1

    async def get_paper(self, arxiv_id: str) -> dict | None:
        """Get paper info including linked repositories."""
        try:
            response = await self._request(
                "GET", f"{self.BASE_URL}/papers/arxiv:{arxiv_id}/"
            )
            paper_data = response.json()

            # Get repositories
            repo_response = await self._request(
                "GET",
                f"{self.BASE_URL}/papers/arxiv:{arxiv_id}/repositories/",
            )
            repos = repo_response.json().get("results", [])

            paper_data["repositories"] = repos
            return paper_data
        except Exception:
            return None

    async def get_repos_for_paper(self, arxiv_id: str) -> list[dict]:
        try:
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/papers/arxiv:{arxiv_id}/repositories/",
            )
            return response.json().get("results", [])
        except Exception:
            return []

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/papers/",
                params={"items_per_page": 1},
            )
            return response.status_code == 200
        except Exception:
            return False
