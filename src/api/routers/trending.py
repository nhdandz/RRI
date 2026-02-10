from fastapi import APIRouter, Query
from sqlalchemy import select

from src.api.deps import DbSession, PaginatedResponse
from src.api.schemas.search import (
    HFFiltersResponse,
    HFKeywordTrend,
    HFModelDetailResponse,
    HFModelResponse,
    HFPaperResponse,
    HFStatsResponse,
    HFTrendingResponse,
    TechRadarResponse,
    TrendingFiltersResponse,
    TrendingPaperResponse,
    TrendingRepoResponse,
)
from src.storage.models.paper import Paper
from src.storage.models.repository import Repository
from src.storage.models.tech_radar import TechRadarSnapshot
from src.storage.repositories.hf_repo import HFModelRepository, HFPaperRepository
from src.storage.repositories.metrics_repo import MetricsRepository

router = APIRouter(prefix="/trending", tags=["Trending"])


@router.get("/filters", response_model=TrendingFiltersResponse)
async def get_trending_filters(db: DbSession):
    metrics = MetricsRepository(db)
    filters = await metrics.get_trending_filters()
    return TrendingFiltersResponse(**filters)


@router.get("/papers", response_model=PaginatedResponse[TrendingPaperResponse])
async def get_trending_papers(
    db: DbSession,
    period: str = Query("week"),
    category: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    metrics = MetricsRepository(db)

    if search:
        rows, total = await metrics.get_trending_papers_with_search(
            category=category, search=search, skip=skip, limit=limit
        )
        if not rows:
            return PaginatedResponse(items=[], total=total, skip=skip, limit=limit)

        items = [
            TrendingPaperResponse(
                id=str(t.entity_id),
                title=paper.title,
                arxiv_id=paper.arxiv_id,
                citation_count=paper.citation_count,
                trending_score=t.total_score,
                category=t.category,
                primary_category=paper.categories[0] if paper.categories else None,
            )
            for t, paper in rows
        ]
        return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)

    trending, total = await metrics.get_trending(
        entity_type="paper", category=category, skip=skip, limit=limit
    )

    if not trending:
        return PaginatedResponse(items=[], total=total, skip=skip, limit=limit)

    entity_ids = [t.entity_id for t in trending]
    result = await db.execute(
        select(Paper).where(Paper.id.in_(entity_ids))
    )
    papers_map = {p.id: p for p in result.scalars().all()}

    items = []
    for t in trending:
        paper = papers_map.get(t.entity_id)
        if not paper:
            continue
        primary_category = paper.categories[0] if paper.categories else None
        items.append(
            TrendingPaperResponse(
                id=str(t.entity_id),
                title=paper.title,
                arxiv_id=paper.arxiv_id,
                citation_count=paper.citation_count,
                trending_score=t.total_score,
                category=t.category,
                primary_category=primary_category,
            )
        )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/repos", response_model=PaginatedResponse[TrendingRepoResponse])
async def get_trending_repos(
    db: DbSession,
    period: str = Query("week"),
    language: str | None = None,
    topic: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    metrics = MetricsRepository(db)
    topics_list = [t.strip() for t in topic.split(",") if t.strip()] if topic else None

    if language or topics_list or search:
        rows, total = await metrics.get_trending_with_language(
            language=language, topics=topics_list, search=search, skip=skip, limit=limit
        )
        if not rows:
            return PaginatedResponse(items=[], total=total, skip=skip, limit=limit)

        items = [
            TrendingRepoResponse(
                id=str(t.entity_id),
                full_name=repo.full_name,
                description=repo.description,
                stars_count=repo.stars_count,
                forks_count=repo.forks_count,
                trending_score=t.total_score,
                primary_language=repo.primary_language,
            )
            for t, repo in rows
        ]
        return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)

    trending, total = await metrics.get_trending(
        entity_type="repository", skip=skip, limit=limit
    )

    if not trending:
        return PaginatedResponse(items=[], total=total, skip=skip, limit=limit)

    entity_ids = [t.entity_id for t in trending]
    result = await db.execute(
        select(Repository).where(Repository.id.in_(entity_ids))
    )
    repos_map = {r.id: r for r in result.scalars().all()}

    items = []
    for t in trending:
        repo = repos_map.get(t.entity_id)
        if not repo:
            continue
        items.append(
            TrendingRepoResponse(
                id=str(t.entity_id),
                full_name=repo.full_name,
                description=repo.description,
                stars_count=repo.stars_count,
                forks_count=repo.forks_count,
                trending_score=t.total_score,
                primary_language=repo.primary_language,
            )
        )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/tech-radar", response_model=TechRadarResponse)
async def get_tech_radar(db: DbSession):
    result = await db.execute(
        select(TechRadarSnapshot)
        .order_by(TechRadarSnapshot.created_at.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        return TechRadarResponse(adopt=[], trial=[], assess=[], hold=[])

    return TechRadarResponse(**snapshot.data)


@router.post("/tech-radar/generate")
async def trigger_tech_radar_generate():
    from src.workers.tasks.reporting import generate_tech_radar

    task = generate_tech_radar.delay()
    return {"task_id": str(task.id), "status": "queued"}


# ── HuggingFace Models (from DB) ──


@router.get("/hf-models", response_model=PaginatedResponse[HFModelResponse])
async def get_hf_models(
    db: DbSession,
    task: str | None = None,
    search: str | None = None,
    sort: str = Query("downloads"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = HFModelRepository(db)
    models, total = await repo.list_models(
        skip=skip, limit=limit, task=task, search=search, sort_by=sort,
    )
    items = [
        HFModelResponse(
            model_id=m.model_id,
            author=m.author,
            downloads=m.downloads,
            likes=m.likes,
            pipeline_tag=m.pipeline_tag,
            architecture=m.architecture,
        )
        for m in models
    ]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/hf-papers", response_model=HFTrendingResponse)
async def get_hf_papers(db: DbSession):
    repo = HFPaperRepository(db)
    papers = await repo.list_recent(limit=100)
    keyword_trends = await repo.get_keyword_trends()

    items = [
        HFPaperResponse(
            title=p.title,
            arxiv_id=p.arxiv_id,
            upvotes=p.upvotes,
            authors=p.authors if isinstance(p.authors, list) else [],
            published_at=str(p.published_at) if p.published_at else None,
        )
        for p in papers
    ]
    trends = [HFKeywordTrend(**kw) for kw in keyword_trends]
    return HFTrendingResponse(papers=items, keyword_trends=trends)


@router.get("/hf-filters", response_model=HFFiltersResponse)
async def get_hf_filters(db: DbSession):
    repo = HFModelRepository(db)
    tags = await repo.get_pipeline_tags()
    if not tags:
        # Fallback to static list if DB is empty
        from src.services.huggingface_service import POPULAR_PIPELINE_TAGS
        tags = POPULAR_PIPELINE_TAGS
    return HFFiltersResponse(pipeline_tags=tags)


@router.get("/hf-stats", response_model=HFStatsResponse)
async def get_hf_stats(db: DbSession):
    repo = HFModelRepository(db)
    stats = await repo.get_stats()
    return HFStatsResponse(**stats)


@router.get("/hf-model-detail/{model_id:path}", response_model=HFModelDetailResponse)
async def get_hf_model_detail(model_id: str, db: DbSession):
    repo = HFModelRepository(db)
    model = await repo.get_by_model_id(model_id)

    if model:
        return HFModelDetailResponse(
            model_id=model.model_id,
            author=model.author,
            downloads=model.downloads,
            likes=model.likes,
            pipeline_tag=model.pipeline_tag,
            architecture=model.architecture,
            model_type=model.model_type,
            library_name=model.library_name,
            tags=model.tags or [],
            languages=model.languages or [],
            license=model.license,
            parameter_count=model.parameter_count,
            created_at=str(model.created_at_hf) if model.created_at_hf else None,
            last_modified=str(model.last_modified_hf) if model.last_modified_hf else None,
        )

    # Fallback to HF API if not in DB
    from src.services.huggingface_service import get_model_detail
    data = await get_model_detail(model_id)
    return HFModelDetailResponse(**data)


@router.post("/hf-models/collect")
async def trigger_collect_hf_models():
    from src.workers.tasks.collection import collect_hf_models

    task = collect_hf_models.delay()
    return {"task_id": str(task.id), "status": "queued"}


@router.post("/hf-papers/collect")
async def trigger_collect_hf_papers():
    from src.workers.tasks.collection import collect_hf_daily_papers

    task = collect_hf_daily_papers.delay()
    return {"task_id": str(task.id), "status": "queued"}
