from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import DbSession, PaginatedResponse
from src.api.schemas.repository import (
    RepositoryDetailResponse,
    RepositoryResponse,
    RepositoryStatsResponse,
)
from src.storage.repositories.github_repo import GitHubRepository
from src.workers.tasks.collection import collect_github_comprehensive, update_existing_repos

router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("/", response_model=PaginatedResponse[RepositoryResponse])
async def list_repositories(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    language: str | None = None,
    topic: str | None = None,
    min_stars: int | None = None,
    search: str | None = None,
    sort_by: str = Query("stars_count"),
    sort_order: str = Query("desc"),
):
    repo = GitHubRepository(db)
    repos, total = await repo.list_repos(
        skip=skip,
        limit=limit,
        language=language,
        topic=topic,
        min_stars=min_stars,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PaginatedResponse(
        items=[RepositoryResponse.model_validate(r) for r in repos],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/topics")
async def list_known_topics():
    """Return curated list of known AI/ML topics for filtering."""
    from src.core.constants import KNOWN_TOPICS

    return {"topics": KNOWN_TOPICS}


@router.get("/stats", response_model=RepositoryStatsResponse)
async def get_repository_stats(
    db: DbSession,
    language: str | None = None,
    topic: str | None = None,
    min_stars: int | None = None,
    search: str | None = None,
):
    repo = GitHubRepository(db)
    stats = await repo.get_stats(
        language=language,
        topic=topic,
        min_stars=min_stars,
        search=search,
    )
    return RepositoryStatsResponse(**stats)


@router.post("/collect")
async def trigger_collect_repos():
    """Trigger comprehensive GitHub repo collection (async via Celery)."""
    task = collect_github_comprehensive.delay()
    return {"task_id": task.id, "status": "started", "message": "Comprehensive collection started"}


@router.post("/update-all")
async def trigger_update_all_repos():
    """Trigger update of all existing repos (async via Celery)."""
    task = update_existing_repos.delay()
    return {"task_id": task.id, "status": "started", "message": "Repo update started"}


@router.get("/{repo_id}", response_model=RepositoryDetailResponse)
async def get_repository(repo_id: UUID, db: DbSession):
    repo_store = GitHubRepository(db)
    repository = await repo_store.get_by_id(repo_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    return RepositoryDetailResponse(
        repo=RepositoryResponse.model_validate(repository),
        linked_papers=[],
        readme_summary=repository.readme_summary,
    )
