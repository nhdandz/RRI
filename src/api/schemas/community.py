from pydantic import BaseModel


# ── Community Posts ──

class CommunityPostResponse(BaseModel):
    id: str
    platform: str
    external_id: str
    title: str | None = None
    body: str | None = None
    url: str | None = None
    author: str | None = None
    author_url: str | None = None
    score: int = 0
    comments_count: int = 0
    shares_count: int = 0
    tags: list[str] = []
    language: str | None = None
    published_at: str | None = None


class CommunityFiltersResponse(BaseModel):
    platforms: list[str] = []
    top_tags: list[dict] = []


class CommunityStatsResponse(BaseModel):
    total_posts: int = 0
    avg_score: float = 0
    platform_counts: dict[str, int] = {}


# ── GitHub Discussions ──

class GitHubDiscussionResponse(BaseModel):
    id: str
    discussion_id: str
    repo_full_name: str
    title: str | None = None
    body: str | None = None
    url: str | None = None
    author: str | None = None
    category: str | None = None
    labels: list[str] = []
    upvotes: int = 0
    comments_count: int = 0
    answer_chosen: bool = False
    published_at: str | None = None


class DiscussionFiltersResponse(BaseModel):
    categories: list[str] = []
    repos: list[str] = []


class DiscussionStatsResponse(BaseModel):
    total: int = 0
    repos_count: int = 0
    category_distribution: dict[str, int] = {}


# ── OpenReview ──

class OpenReviewResponse(BaseModel):
    id: str
    note_id: str
    forum_id: str | None = None
    title: str | None = None
    abstract: str | None = None
    tldr: str | None = None
    authors: list[str] = []
    venue: str | None = None
    primary_area: str | None = None
    average_rating: float | None = None
    review_count: int = 0
    reviews_fetched: bool = False
    keywords: list[str] = []
    pdf_url: str | None = None
    paper_id: str | None = None
    published_at: str | None = None


class OpenReviewFiltersResponse(BaseModel):
    venues: list[str] = []
    primary_areas: list[str] = []


class OpenReviewStatsResponse(BaseModel):
    total: int = 0
    avg_rating: float = 0
    reviewed_count: int = 0
    linked_count: int = 0
    venue_distribution: dict[str, int] = {}
    area_distribution: dict[str, int] = {}


# ── Shared ──

class KeywordTrend(BaseModel):
    keyword: str
    count: int
