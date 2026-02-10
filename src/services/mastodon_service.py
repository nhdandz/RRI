"""Mastodon API client for public timelines."""

from datetime import datetime

import httpx

DEFAULT_INSTANCES = ["mastodon.social", "sigmoid.social"]
AI_HASHTAGS = ["machinelearning", "ai", "llm", "deeplearning", "datascience"]


async def fetch_mastodon_timeline(
    instance: str = "mastodon.social",
    limit: int = 40,
    hashtag: str | None = None,
) -> list[dict]:
    """Fetch public timeline or hashtag timeline from a Mastodon instance."""
    if hashtag:
        url = f"https://{instance}/api/v1/timelines/tag/{hashtag}"
    else:
        url = f"https://{instance}/api/v1/timelines/public"

    params = {"limit": min(limit, 40), "local": "false"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()

    posts = []
    for status in raw:
        status_id = str(status.get("id", ""))
        if not status_id:
            continue

        created_at_str = status.get("created_at")
        published_at = None
        if created_at_str:
            try:
                published_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        account = status.get("account") or {}
        tags = [t.get("name", "") for t in (status.get("tags") or []) if t.get("name")]

        # Use content as body (HTML stripped lightly)
        content = status.get("content") or ""

        posts.append({
            "platform": "mastodon",
            "external_id": f"{instance}:{status_id}",
            "title": content[:200] if content else "",
            "body": content,
            "url": status.get("url") or status.get("uri", ""),
            "author": account.get("acct") or account.get("username", ""),
            "author_url": account.get("url", ""),
            "score": status.get("favourites_count") or 0,
            "comments_count": status.get("replies_count") or 0,
            "shares_count": status.get("reblogs_count") or 0,
            "tags": tags,
            "language": status.get("language"),
            "extra": {
                "instance": instance,
                "sensitive": status.get("sensitive"),
                "visibility": status.get("visibility"),
                "media_count": len(status.get("media_attachments") or []),
            },
            "published_at": published_at,
        })

    return posts


async def fetch_all_mastodon_ai_posts() -> list[dict]:
    """Fetch AI-related posts from multiple Mastodon instances and hashtags."""
    all_posts = []
    seen_ids: set[str] = set()

    for instance in DEFAULT_INSTANCES:
        for hashtag in AI_HASHTAGS:
            try:
                posts = await fetch_mastodon_timeline(
                    instance=instance, hashtag=hashtag, limit=40
                )
                for p in posts:
                    if p["external_id"] not in seen_ids:
                        seen_ids.add(p["external_id"])
                        all_posts.append(p)
            except Exception:
                continue

    return all_posts
