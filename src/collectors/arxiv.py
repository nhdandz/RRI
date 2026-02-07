"""
ArXiv API Collector

API Docs: https://info.arxiv.org/help/api/index.html
Rate Limit: 1 request per 3 seconds
"""

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime

from src.collectors.base import BaseCollector, CollectorConfig, CollectorResult
from src.core.logging import get_logger

logger = get_logger(__name__)


def _parse_date(date_str: str) -> date:
    return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[dict]
    categories: list[str]
    published_date: date
    updated_date: date
    pdf_url: str
    comment: str | None = None


class ArxivCollector(BaseCollector):
    """
    Collects papers from ArXiv API.

    Usage:
        async with ArxivCollector() as collector:
            async for paper in collector.collect(
                categories=["cs.AI", "cs.CL"],
                date_from=date(2024, 1, 1),
                max_results=100
            ):
                process(paper)
    """

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self):
        super().__init__(
            CollectorConfig(
                name="arxiv",
                base_url=self.BASE_URL,
                rate_limit_per_minute=20,
            )
        )

    def _get_headers(self) -> dict:
        return {"User-Agent": "OSINT-Research-Bot/1.0"}

    async def collect(
        self,
        categories: list[str] | None = None,
        search_query: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        max_results: int = 100,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> AsyncIterator[CollectorResult[ArxivPaper]]:
        query = self._build_query(categories, search_query, date_from, date_to)

        start = 0
        batch_size = min(100, max_results)

        while start < max_results:
            params = {
                "search_query": query,
                "start": start,
                "max_results": batch_size,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }

            response = await self._request("GET", self.BASE_URL, params=params)
            papers = self._parse_response(response.text)

            if not papers:
                break

            for paper in papers:
                yield CollectorResult(
                    data=paper,
                    source="arxiv",
                    collected_at=datetime.utcnow(),
                )

            start += len(papers)
            if len(papers) < batch_size:
                break

    def _build_query(
        self,
        categories: list[str] | None,
        search_query: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> str:
        parts = []

        if categories:
            cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
            parts.append(f"({cat_query})")

        if search_query:
            parts.append(f"all:{search_query}")

        if date_from or date_to:
            from_str = date_from.strftime("%Y%m%d0000") if date_from else "*"
            to_str = date_to.strftime("%Y%m%d2359") if date_to else "*"
            parts.append(f"submittedDate:[{from_str} TO {to_str}]")

        return " AND ".join(parts) if parts else "all:*"

    def _parse_response(self, xml_content: str) -> list[ArxivPaper]:
        root = ET.fromstring(xml_content)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        papers = []
        for entry in root.findall("atom:entry", ns):
            id_url = entry.find("atom:id", ns).text
            arxiv_id = id_url.split("/abs/")[-1]

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text
                affiliation = author.find("arxiv:affiliation", ns)
                authors.append(
                    {
                        "name": name,
                        "affiliation": affiliation.text
                        if affiliation is not None
                        else None,
                    }
                )

            categories = [
                cat.get("term") for cat in entry.findall("atom:category", ns)
            ]

            comment_el = entry.find("arxiv:comment", ns)

            papers.append(
                ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=entry.find("atom:title", ns).text.strip(),
                    abstract=entry.find("atom:summary", ns).text.strip(),
                    authors=authors,
                    categories=categories,
                    published_date=_parse_date(
                        entry.find("atom:published", ns).text
                    ),
                    updated_date=_parse_date(
                        entry.find("atom:updated", ns).text
                    ),
                    pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    comment=comment_el.text if comment_el is not None else None,
                )
            )

        return papers

    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET",
                self.BASE_URL,
                params={"search_query": "all:test", "max_results": 1},
            )
            return response.status_code == 200
        except Exception:
            return False
