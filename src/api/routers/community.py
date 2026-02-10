from fastapi import APIRouter, Query

from src.api.deps import DbSession, PaginatedResponse
from src.api.schemas.community import (
    CommunityFiltersResponse,
    CommunityPostResponse,
    CommunityStatsResponse,
    DiscussionFiltersResponse,
    DiscussionStatsResponse,
    GitHubDiscussionResponse,
    KeywordTrend,
    OpenReviewFiltersResponse,
    OpenReviewResponse,
    OpenReviewStatsResponse,
)
from src.storage.repositories.community_repo import CommunityPostRepository
from src.storage.repositories.github_discussion_repo import GitHubDiscussionRepository
from src.storage.repositories.openreview_repo import OpenReviewRepository

router = APIRouter(prefix="/community", tags=["Community"])


# ── Community Posts ──


@router.get("/posts", response_model=PaginatedResponse[CommunityPostResponse])
async def get_community_posts(
    db: DbSession,
    platform: str | None = None,
    search: str | None = None,
    tag: str | None = None,
    sort: str = Query("score"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = CommunityPostRepository(db)
    posts, total = await repo.list_posts(
        skip=skip, limit=limit, platform=platform,
        search=search, tag=tag, sort_by=sort, sort_order=sort_order,
    )
    items = [
        CommunityPostResponse(
            id=str(p.id),
            platform=p.platform,
            external_id=p.external_id,
            title=p.title,
            body=(p.body or "")[:500] if p.body else None,
            url=p.url,
            author=p.author,
            author_url=p.author_url,
            score=p.score,
            comments_count=p.comments_count,
            shares_count=p.shares_count,
            tags=p.tags or [],
            language=p.language,
            published_at=str(p.published_at) if p.published_at else None,
        )
        for p in posts
    ]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/posts/filters", response_model=CommunityFiltersResponse)
async def get_community_filters(db: DbSession):
    repo = CommunityPostRepository(db)
    platforms = await repo.get_platforms()
    top_tags = await repo.get_top_tags(limit=20)
    return CommunityFiltersResponse(platforms=platforms, top_tags=top_tags)


@router.get("/posts/stats", response_model=CommunityStatsResponse)
async def get_community_stats(
    db: DbSession,
    platform: str | None = None,
):
    repo = CommunityPostRepository(db)
    stats = await repo.get_stats(platform=platform)
    return CommunityStatsResponse(**stats)


@router.get("/posts/keywords", response_model=list[KeywordTrend])
async def get_community_keywords(
    db: DbSession,
    platform: str | None = None,
    limit: int = Query(15, ge=1, le=50),
):
    repo = CommunityPostRepository(db)
    trends = await repo.get_keyword_trends(platform=platform, limit=limit)
    return [KeywordTrend(**t) for t in trends]


@router.post("/posts/collect")
async def trigger_collect_community():
    from src.workers.tasks.collection import collect_all_community
    task = collect_all_community.delay()
    return {"task_id": str(task.id), "status": "queued"}


# ── GitHub Discussions ──


@router.get("/discussions", response_model=PaginatedResponse[GitHubDiscussionResponse])
async def get_discussions(
    db: DbSession,
    repo_name: str | None = Query(None, alias="repo"),
    category: str | None = None,
    search: str | None = None,
    sort: str = Query("upvotes"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = GitHubDiscussionRepository(db)
    discussions, total = await repo.list_discussions(
        skip=skip, limit=limit, repo=repo_name,
        category=category, search=search, sort_by=sort, sort_order=sort_order,
    )
    items = [
        GitHubDiscussionResponse(
            id=str(d.id),
            discussion_id=d.discussion_id,
            repo_full_name=d.repo_full_name,
            title=d.title,
            body=(d.body or "")[:500] if d.body else None,
            url=d.url,
            author=d.author,
            category=d.category,
            labels=d.labels or [],
            upvotes=d.upvotes,
            comments_count=d.comments_count,
            answer_chosen=d.answer_chosen,
            published_at=str(d.published_at) if d.published_at else None,
        )
        for d in discussions
    ]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/discussions/filters", response_model=DiscussionFiltersResponse)
async def get_discussion_filters(db: DbSession):
    repo = GitHubDiscussionRepository(db)
    categories = await repo.get_categories()
    repos = await repo.get_repos()
    return DiscussionFiltersResponse(categories=categories, repos=repos)


@router.get("/discussions/stats", response_model=DiscussionStatsResponse)
async def get_discussion_stats(db: DbSession):
    repo = GitHubDiscussionRepository(db)
    stats = await repo.get_stats()
    return DiscussionStatsResponse(**stats)


@router.post("/discussions/collect")
async def trigger_collect_discussions():
    from src.workers.tasks.collection import collect_github_discussions
    task = collect_github_discussions.delay()
    return {"task_id": str(task.id), "status": "queued"}


# ── OpenReview ──


@router.get("/openreview", response_model=PaginatedResponse[OpenReviewResponse])
async def get_openreview_notes(
    db: DbSession,
    venue: str | None = None,
    primary_area: str | None = None,
    search: str | None = None,
    min_rating: float | None = None,
    sort: str = Query("average_rating"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    repo = OpenReviewRepository(db)
    notes, total = await repo.list_notes(
        skip=skip, limit=limit, venue=venue, primary_area=primary_area,
        search=search, min_rating=min_rating, sort_by=sort, sort_order=sort_order,
    )
    items = [
        OpenReviewResponse(
            id=str(n.id),
            note_id=n.note_id,
            forum_id=n.forum_id,
            title=n.title,
            abstract=(n.abstract or "")[:500] if n.abstract else None,
            tldr=n.tldr,
            authors=n.authors or [],
            venue=n.venue,
            primary_area=n.primary_area,
            average_rating=n.average_rating,
            review_count=n.review_count,
            reviews_fetched=n.reviews_fetched,
            keywords=n.keywords or [],
            pdf_url=n.pdf_url,
            paper_id=str(n.paper_id) if n.paper_id else None,
            published_at=str(n.published_at) if n.published_at else None,
        )
        for n in notes
    ]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/openreview/filters", response_model=OpenReviewFiltersResponse)
async def get_openreview_filters(db: DbSession):
    repo = OpenReviewRepository(db)
    venues = await repo.get_venues()
    primary_areas = await repo.get_primary_areas()
    return OpenReviewFiltersResponse(venues=venues, primary_areas=primary_areas)


@router.get("/openreview/stats", response_model=OpenReviewStatsResponse)
async def get_openreview_stats(db: DbSession):
    repo = OpenReviewRepository(db)
    stats = await repo.get_stats()
    return OpenReviewStatsResponse(**stats)


@router.get("/openreview/keywords", response_model=list[KeywordTrend])
async def get_openreview_keywords(
    db: DbSession,
    limit: int = Query(15, ge=1, le=50),
):
    repo = OpenReviewRepository(db)
    trends = await repo.get_keyword_trends(limit=limit)
    return [KeywordTrend(**t) for t in trends]


@router.post("/openreview/collect")
async def trigger_collect_openreview():
    from src.workers.tasks.collection import collect_openreview
    task = collect_openreview.delay()
    return {"task_id": str(task.id), "status": "queued"}
