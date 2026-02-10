"""Hacker News API client via Algolia search."""

from datetime import datetime

import httpx

HN_API_BASE = "https://hn.algolia.com/api/v1"

AI_QUERIES = ["AI", "machine learning", "LLM", "deep learning", "GPT", "transformer"]


async def fetch_hn_top_stories(
    query: str = "AI",
    tags: str = "story",
    num_results: int = 100,
) -> list[dict]:
    """Fetch top stories from HN Algolia API and normalize to CommunityPost format."""
    params = {
        "query": query,
        "tags": tags,
        "hitsPerPage": min(num_results, 200),
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{HN_API_BASE}/search", params=params)
        resp.raise_for_status()
        raw = resp.json()

    posts = []
    for hit in raw.get("hits", []):
        object_id = hit.get("objectID", "")
        if not object_id:
            continue

        created_at_str = hit.get("created_at")
        published_at = None
        if created_at_str:
            try:
                published_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        posts.append({
            "platform": "hackernews",
            "external_id": object_id,
            "title": hit.get("title") or "",
            "body": hit.get("story_text"),
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
            "author": hit.get("author"),
            "author_url": f"https://news.ycombinator.com/user?id={hit.get('author', '')}",
            "score": hit.get("points") or 0,
            "comments_count": hit.get("num_comments") or 0,
            "shares_count": 0,
            "tags": hit.get("_tags", []),
            "language": "en",
            "extra": {
                "relevancy_score": hit.get("relevancy_score"),
            },
            "published_at": published_at,
        })

    return posts


async def fetch_all_hn_ai_stories(num_per_query: int = 100) -> list[dict]:
    """Fetch HN stories for all AI-related queries."""
    all_posts = []
    seen_ids: set[str] = set()

    for query in AI_QUERIES:
        try:
            posts = await fetch_hn_top_stories(query=query, num_results=num_per_query)
            for p in posts:
                if p["external_id"] not in seen_ids:
                    seen_ids.add(p["external_id"])
                    all_posts.append(p)
        except Exception:
            continue

    return all_posts
