"""
OpenAlex API Collector

API Docs: https://docs.openalex.org/
Rate Limit: 100,000 requests/day (with polite pool)
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OpenAlexWork:
    openalex_id: str
    doi: str | None
    title: str
    abstract: str | None
    authors: list[dict]
    publication_year: int | None
    cited_by_count: int
    concepts: list[dict]
    is_open_access: bool
    source_name: str | None = None


class OpenAlexCollector(BaseCollector):
    """Collects research works from OpenAlex API."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, email: str | None = None):
        self.email = email
        super().__init__(
            CollectorConfig(
                name="openalex",
                base_url=self.BASE_URL,
                rate_limit_per_minute=100,
            )
        )

    def _get_headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.email:
            headers["User-Agent"] = f"mailto:{self.email}"
        return headers

    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult[OpenAlexWork]]:
        async for result in self.search(**kwargs):
            yield result

    async def search(
        self,
        query: str = "",
        concept_id: str | None = None,
        from_year: int | None = None,
        min_citations: int | None = None,
        max_results: int = 100,
    ) -> AsyncIterator[CollectorResult[OpenAlexWork]]:
        params: dict = {"per_page": min(200, max_results)}

        if query:
            params["search"] = query

        filters = []
        if concept_id:
            filters.append(f"concepts.id:{concept_id}")
        if from_year:
            filters.append(f"publication_year:>{from_year}")
        if min_citations:
            filters.append(f"cited_by_count:>{min_citations}")
        if filters:
            params["filter"] = ",".join(filters)

        if self.email:
            params["mailto"] = self.email

        response = await self._request(
            "GET", f"{self.BASE_URL}/works", params=params
        )

        data = response.json()
        for item in data.get("results", []):
            work = self._parse_work(item)
            yield CollectorResult(
                data=work,
                source="openalex",
                collected_at=datetime.utcnow(),
            )

    def _parse_work(self, data: dict) -> OpenAlexWork:
        authors = []
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            institution = (authorship.get("institutions") or [{}])[0] if authorship.get("institutions") else {}
            authors.append({
                "name": author.get("display_name", ""),
                "affiliation": institution.get("display_name"),
            })

        concepts = [
            {"name": c.get("display_name", ""), "score": c.get("score", 0)}
            for c in (data.get("concepts") or [])[:10]
        ]

        # Reconstruct abstract from inverted index
        abstract = None
        abstract_index = data.get("abstract_inverted_index")
        if abstract_index:
            positions = {}
            for word, indices in abstract_index.items():
                for idx in indices:
                    positions[idx] = word
            if positions:
                abstract = " ".join(positions[i] for i in sorted(positions.keys()))

        oa = data.get("open_access", {})

        return OpenAlexWork(
            openalex_id=data.get("id", ""),
            doi=data.get("doi"),
            title=data.get("title", ""),
            abstract=abstract,
            authors=authors,
            publication_year=data.get("publication_year"),
            cited_by_count=data.get("cited_by_count", 0),
            concepts=concepts,
            is_open_access=oa.get("is_oa", False),
            source_name=data.get("primary_location", {}).get("source", {}).get("display_name") if data.get("primary_location") else None,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET", f"{self.BASE_URL}/works", params={"per_page": 1}
            )
            return response.status_code == 200
        except Exception:
            return False
