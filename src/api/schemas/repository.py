from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RepositoryResponse(BaseModel):
    id: UUID
    full_name: str
    name: str
    owner: str
    description: str | None = None
    html_url: str
    primary_language: str | None = None
    topics: list[str] | None = None
    frameworks: list[str] | None = None
    stars_count: int = 0
    forks_count: int = 0
    watchers_count: int = 0
    open_issues_count: int = 0
    last_commit_at: datetime | None = None
    last_release_tag: str | None = None
    has_readme: bool = False
    has_license: bool = False
    has_docker: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class RepositoryStatsResponse(BaseModel):
    total_repos: int
    total_stars: int
    avg_stars: float
    active_repos: int
    language_distribution: dict[str, int]
    topic_distribution: dict[str, int]


class RepositoryDetailResponse(BaseModel):
    repo: RepositoryResponse
    linked_papers: list[dict] = []
    readme_summary: str | None = None
