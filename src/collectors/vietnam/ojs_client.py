"""OJS (Open Journal Systems) API client for Vietnamese journals."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OJSArticle:
    article_id: str
    title: str
    abstract: str | None
    authors: list[dict]
    published_date: date | None
    journal_name: str
    doi: str | None = None
    keywords: list[str] | None = None
    url: str | None = None
    pdf_url: str | None = None


class OJSClient(BaseCollector):
    """Client for OJS-based Vietnamese journal APIs."""

    def __init__(self, base_url: str, journal_name: str):
        self.journal_name = journal_name
        super().__init__(
            CollectorConfig(
                name=f"ojs_{journal_name}",
                base_url=base_url,
                rate_limit_per_minute=10,
            )
        )

    def _get_headers(self) -> dict:
        return {"Accept": "application/json"}

    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult[OJSArticle]]:
        async for result in self.search_articles(**kwargs):
            yield result

    async def search_articles(
        self, query: str = "", max_results: int = 50
    ) -> AsyncIterator[CollectorResult[OJSArticle]]:
        try:
            params = {"searchPhrase": query} if query else {}
            response = await self._request(
                "GET",
                f"{self.config.base_url}/api/v1/submissions",
                params=params,
            )

            data = response.json()
            items = data.get("items", []) if isinstance(data, dict) else data

            for item in items[:max_results]:
                article = self._parse_article(item)
                if article:
                    yield CollectorResult(
                        data=article,
                        source=f"ojs_{self.journal_name}",
                        collected_at=datetime.utcnow(),
                    )
        except Exception as e:
            logger.warning("OJS collection failed", journal=self.journal_name, error=str(e))

    def _parse_article(self, data: dict) -> OJSArticle | None:
        try:
            pub = data.get("publications", [{}])[0] if data.get("publications") else {}
            title = pub.get("title", {})
            title_text = title.get("vi") or title.get("en") or str(title)

            abstract = pub.get("abstract", {})
            abstract_text = abstract.get("vi") or abstract.get("en") or ""

            authors = []
            for author_data in pub.get("authors", []):
                given = author_data.get("givenName", {})
                family = author_data.get("familyName", {})
                name = f"{given.get('vi', given.get('en', ''))} {family.get('vi', family.get('en', ''))}".strip()
                authors.append({"name": name, "affiliation": author_data.get("affiliation", {}).get("vi")})

            return OJSArticle(
                article_id=str(data.get("id", "")),
                title=title_text,
                abstract=abstract_text if abstract_text else None,
                authors=authors,
                published_date=None,
                journal_name=self.journal_name,
                doi=pub.get("pub-id::doi"),
                keywords=pub.get("keywords", {}).get("vi", []),
            )
        except Exception:
            return None

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET", f"{self.config.base_url}/api/v1/submissions", params={"count": 1}
            )
            return response.status_code == 200
        except Exception:
            return False
