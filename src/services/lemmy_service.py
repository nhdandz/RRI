"""Lemmy API client for community posts."""

from datetime import datetime

import httpx

DEFAULT_INSTANCES = ["lemmy.world", "lemmy.ml"]
AI_COMMUNITIES = ["programming", "machinelearning", "artificial_intelligence", "technology"]


async def fetch_lemmy_posts(
    instance: str = "lemmy.world",
    sort: str = "Active",
    community: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch posts from a Lemmy instance and normalize to CommunityPost format."""
    url = f"https://{instance}/api/v3/post/list"
    params: dict = {
        "sort": sort,
        "limit": min(limit, 50),
        "type_": "All",
    }
    if community:
        params["community_name"] = community

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()

    posts = []
    for item in raw.get("posts", []):
        post = item.get("post") or {}
        counts = item.get("counts") or {}
        creator = item.get("creator") or {}
        community_info = item.get("community") or {}

        post_id = str(post.get("id", ""))
        if not post_id:
            continue

        published_str = post.get("published")
        published_at = None
        if published_str:
            try:
                published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass

        community_name = community_info.get("name", "")

        posts.append({
            "platform": "lemmy",
            "external_id": f"{instance}:{post_id}",
            "title": post.get("name") or "",
            "body": post.get("body"),
            "url": post.get("url") or post.get("ap_id", ""),
            "author": creator.get("name", ""),
            "author_url": creator.get("actor_id", ""),
            "score": counts.get("score") or 0,
            "comments_count": counts.get("comments") or 0,
            "shares_count": 0,
            "tags": [community_name] if community_name else [],
            "language": None,
            "extra": {
                "instance": instance,
                "community": community_name,
                "community_title": community_info.get("title"),
                "nsfw": post.get("nsfw", False),
                "upvotes": counts.get("upvotes", 0),
                "downvotes": counts.get("downvotes", 0),
            },
            "published_at": published_at,
        })

    return posts


async def fetch_all_lemmy_ai_posts() -> list[dict]:
    """Fetch AI-related posts from multiple Lemmy instances and communities."""
    all_posts = []
    seen_ids: set[str] = set()

    for instance in DEFAULT_INSTANCES:
        # General active posts
        try:
            posts = await fetch_lemmy_posts(instance=instance, sort="Active", limit=50)
            for p in posts:
                if p["external_id"] not in seen_ids:
                    seen_ids.add(p["external_id"])
                    all_posts.append(p)
        except Exception:
            continue

        # Community-specific
        for community in AI_COMMUNITIES:
            try:
                posts = await fetch_lemmy_posts(
                    instance=instance, community=community, sort="Active", limit=50
                )
                for p in posts:
                    if p["external_id"] not in seen_ids:
                        seen_ids.add(p["external_id"])
                        all_posts.append(p)
            except Exception:
                continue

    return all_posts
