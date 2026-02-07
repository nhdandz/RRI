from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class PaperResponse(BaseModel):
    id: UUID
    arxiv_id: str | None = None
    doi: str | None = None
    title: str
    abstract: str | None = None
    summary: str | None = None
    authors: list[dict] | None = None
    categories: list[str] | None = None
    topics: list[str] | None = None
    keywords: list[str] | None = None
    published_date: date | None = None
    source: str
    source_url: str | None = None
    pdf_url: str | None = None
    citation_count: int = 0
    influential_citation_count: int = 0
    is_vietnamese: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class PaperStatsResponse(BaseModel):
    total_papers: int = 0
    total_citations: int = 0
    avg_citations: float = 0.0
    recent_papers: int = 0
    category_distribution: dict[str, int] = {}
    source_distribution: dict[str, int] = {}
    year_distribution: dict[str, int] = {}


class PaperDetailResponse(BaseModel):
    paper: PaperResponse
    linked_repos: list[dict] = []


class LinkResponse(BaseModel):
    id: UUID
    repo_id: UUID
    link_type: str
    confidence_score: float
    discovered_via: str | None = None

    model_config = {"from_attributes": True}
