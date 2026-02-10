"""Dev.to API client."""

from datetime import datetime

import httpx

DEVTO_API_BASE = "https://dev.to/api"


async def fetch_devto_articles(
    top: int = 7,
    per_page: int = 100,
    page: int = 1,
    tag: str | None = None,
) -> list[dict]:
    """Fetch top articles from Dev.to and normalize to CommunityPost format."""
    params: dict = {
        "top": top,
        "per_page": min(per_page, 1000),
        "page": page,
    }
    if tag:
        params["tag"] = tag

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DEVTO_API_BASE}/articles", params=params)
        resp.raise_for_status()
        raw = resp.json()

    posts = []
    for article in raw:
        article_id = str(article.get("id", ""))
        if not article_id:
            continue

        published_at_str = article.get("published_at")
        published_at = None
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        tag_list = article.get("tag_list", [])
        if isinstance(tag_list, str):
            tag_list = [t.strip() for t in tag_list.split(",") if t.strip()]

        user = article.get("user") or {}

        posts.append({
            "platform": "devto",
            "external_id": article_id,
            "title": article.get("title") or "",
            "body": article.get("description"),
            "url": article.get("url") or "",
            "author": user.get("username") or article.get("user", {}).get("name", ""),
            "author_url": f"https://dev.to/{user.get('username', '')}",
            "score": article.get("positive_reactions_count") or 0,
            "comments_count": article.get("comments_count") or 0,
            "shares_count": 0,
            "tags": tag_list,
            "language": "en",
            "extra": {
                "reading_time_minutes": article.get("reading_time_minutes"),
                "cover_image": article.get("cover_image"),
                "type_of": article.get("type_of"),
            },
            "published_at": published_at,
        })

    return posts


AI_TAGS = ["ai", "machinelearning", "deeplearning", "llm", "python", "datascience"]


async def fetch_all_devto_ai_articles() -> list[dict]:
    """Fetch Dev.to articles for AI-related tags."""
    all_posts = []
    seen_ids: set[str] = set()

    # General top articles
    try:
        posts = await fetch_devto_articles(top=7, per_page=100)
        for p in posts:
            if p["external_id"] not in seen_ids:
                seen_ids.add(p["external_id"])
                all_posts.append(p)
    except Exception:
        pass

    # Tag-specific
    for tag in AI_TAGS:
        try:
            posts = await fetch_devto_articles(top=7, per_page=50, tag=tag)
            for p in posts:
                if p["external_id"] not in seen_ids:
                    seen_ids.add(p["external_id"])
                    all_posts.append(p)
        except Exception:
            continue

    return all_posts
