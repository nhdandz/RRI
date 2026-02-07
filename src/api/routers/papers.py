from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import DbSession, PaginatedResponse
from src.api.schemas.paper import PaperDetailResponse, PaperResponse, PaperStatsResponse
from src.storage.repositories.paper_repo import PaperRepository
from src.workers.tasks.collection import collect_arxiv_papers, collect_papers_comprehensive, collect_papers_s2, enrich_paper_citations

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.get("/", response_model=PaginatedResponse[PaperResponse])
async def list_papers(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    topic: str | None = None,
    search: str | None = None,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    has_code: bool | None = None,
    is_vietnamese: bool | None = None,
    sort_by: str = Query("published_date"),
    sort_order: str = Query("desc"),
):
    repo = PaperRepository(db)
    papers, total = await repo.list_papers(
        skip=skip,
        limit=limit,
        category=category,
        topic=topic,
        search=search,
        source=source,
        date_from=date_from,
        date_to=date_to,
        has_code=has_code,
        is_vietnamese=is_vietnamese,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PaginatedResponse(
        items=[PaperResponse.model_validate(p) for p in papers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=PaperStatsResponse)
async def get_paper_stats(
    db: DbSession,
    category: str | None = None,
    topic: str | None = None,
    search: str | None = None,
    source: str | None = None,
):
    repo = PaperRepository(db)
    stats = await repo.get_stats(
        category=category,
        topic=topic,
        search=search,
        source=source,
    )
    return PaperStatsResponse(**stats)


@router.get("/categories")
async def list_paper_categories(db: DbSession):
    """Return all known paper categories from the database."""
    repo = PaperRepository(db)
    stats = await repo.get_stats()
    categories = sorted(stats["category_distribution"].keys())
    return {"categories": categories}


@router.post("/collect")
async def trigger_collect_papers():
    """Trigger comprehensive paper collection from ArXiv + Semantic Scholar."""
    task = collect_papers_comprehensive.delay()
    return {"task_id": task.id, "status": "started", "message": "Comprehensive paper collection started (ArXiv + Semantic Scholar)"}


@router.post("/collect-s2")
async def trigger_collect_s2():
    """Trigger Semantic Scholar paper collection separately."""
    task = collect_papers_s2.delay()
    return {"task_id": task.id, "status": "started", "message": "Semantic Scholar paper collection started (960 queries)"}


@router.post("/enrich-citations")
async def trigger_enrich_citations():
    """Enrich papers with citation data from Semantic Scholar."""
    task = enrich_paper_citations.delay()
    return {"task_id": task.id, "status": "started", "message": "Citation enrichment started via Semantic Scholar Batch API"}


@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper(paper_id: UUID, db: DbSession):
    repo = PaperRepository(db)
    paper = await repo.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return PaperDetailResponse(
        paper=PaperResponse.model_validate(paper),
        linked_repos=[],
    )
