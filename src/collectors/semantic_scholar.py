"""
Semantic Scholar API Collector

API Docs: https://api.semanticscholar.org/
Rate Limit: 100 requests/5 min (authenticated), 10/5min (unauthenticated)
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)

S2_FIELDS = (
    "paperId,externalIds,title,abstract,authors,year,venue,"
    "citationCount,influentialCitationCount,referenceCount,"
    "fieldsOfStudy,isOpenAccess"
)


@dataclass
class SemanticScholarPaper:
    s2_id: str
    arxiv_id: str | None
    doi: str | None
    title: str
    abstract: str | None
    authors: list[dict]
    year: int | None
    venue: str | None
    citation_count: int
    influential_citation_count: int
    references_count: int
    fields_of_study: list[str]
    is_open_access: bool
    external_ids: dict = field(default_factory=dict)


class SemanticScholarCollector(BaseCollector):
    """
    Collects paper metadata and citations from Semantic Scholar.

    Best used for:
    - Enriching ArXiv papers with citation data
    - Finding influential papers
    - Building citation graphs
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        super().__init__(
            CollectorConfig(
                name="semantic_scholar",
                base_url=self.BASE_URL,
                rate_limit_per_minute=20 if api_key else 2,
            )
        )

    def _get_headers(self) -> dict:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult[SemanticScholarPaper]]:
        async for result in self.search(**kwargs):
            yield result

    async def search(
        self,
        query: str = "",
        year_range: tuple[int, int] | None = None,
        fields_of_study: list[str] | None = None,
        open_access_only: bool = False,
        max_results: int = 100,
    ) -> AsyncIterator[CollectorResult[SemanticScholarPaper]]:
        offset = 0
        limit = min(100, max_results)

        while offset < max_results:
            params = {
                "query": query,
                "fields": S2_FIELDS,
                "offset": offset,
                "limit": limit,
            }

            if year_range:
                params["year"] = f"{year_range[0]}-{year_range[1]}"
            if fields_of_study:
                params["fieldsOfStudy"] = ",".join(fields_of_study)
            if open_access_only:
                params["openAccessPdf"] = ""

            response = await self._request(
                "GET", f"{self.BASE_URL}/paper/search", params=params
            )

            data = response.json()
            papers = data.get("data", [])

            if not papers:
                break

            for paper_data in papers:
                paper = self._parse_paper(paper_data)
                yield CollectorResult(
                    data=paper,
                    source="semantic_scholar",
                    collected_at=datetime.utcnow(),
                )

            offset += len(papers)
            if len(papers) < limit:
                break

    async def get_paper(self, paper_id: str) -> SemanticScholarPaper | None:
        """Get a single paper. paper_id can be S2 ID, arxiv:XXX, or doi:XXX."""
        try:
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/paper/{paper_id}",
                params={"fields": S2_FIELDS},
            )
            return self._parse_paper(response.json())
        except Exception:
            return None

    async def get_papers_batch(
        self, paper_ids: list[str]
    ) -> list[SemanticScholarPaper]:
        results = []
        for i in range(0, len(paper_ids), 500):
            batch = paper_ids[i : i + 500]
            response = await self._request(
                "POST",
                f"{self.BASE_URL}/paper/batch",
                params={"fields": S2_FIELDS},
                json={"ids": batch},
            )
            for paper_data in response.json():
                if paper_data:
                    results.append(self._parse_paper(paper_data))
        return results

    async def get_citations(
        self, paper_id: str, max_results: int = 100
    ) -> list[SemanticScholarPaper]:
        results = []
        offset = 0
        while offset < max_results:
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/paper/{paper_id}/citations",
                params={
                    "fields": S2_FIELDS,
                    "offset": offset,
                    "limit": min(100, max_results - offset),
                },
            )
            data = response.json().get("data", [])
            if not data:
                break
            for item in data:
                citing = item.get("citingPaper")
                if citing:
                    results.append(self._parse_paper(citing))
            offset += len(data)
        return results

    def _parse_paper(self, data: dict) -> SemanticScholarPaper:
        external_ids = data.get("externalIds", {})
        authors = [
            {"name": a.get("name"), "author_id": a.get("authorId")}
            for a in (data.get("authors") or [])
        ]

        return SemanticScholarPaper(
            s2_id=data["paperId"],
            arxiv_id=external_ids.get("ArXiv"),
            doi=external_ids.get("DOI"),
            title=data.get("title", ""),
            abstract=data.get("abstract"),
            authors=authors,
            year=data.get("year"),
            venue=data.get("venue"),
            citation_count=data.get("citationCount", 0),
            influential_citation_count=data.get("influentialCitationCount", 0),
            references_count=data.get("referenceCount", 0),
            fields_of_study=data.get("fieldsOfStudy") or [],
            is_open_access=data.get("isOpenAccess", False),
            external_ids=external_ids,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET", f"{self.BASE_URL}/paper/arxiv:2301.00001"
            )
            return response.status_code == 200
        except Exception:
            return False
