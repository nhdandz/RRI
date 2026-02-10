import re
from collections import Counter

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.community_post import CommunityPost

STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with", "on",
    "is", "are", "was", "were", "be", "been", "being", "by", "at", "from",
    "as", "into", "through", "its", "it", "this", "that", "these", "those",
    "not", "but", "if", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "has", "have", "had", "no",
    "nor", "so", "than", "too", "very", "just", "about", "above", "after",
    "again", "all", "also", "am", "any", "because", "before", "between",
    "both", "each", "few", "further", "here", "how", "i", "me", "more",
    "most", "my", "new", "now", "only", "other", "our", "out", "own",
    "same", "she", "he", "some", "such", "there", "then", "their", "them",
    "they", "we", "what", "when", "where", "which", "while", "who", "whom",
    "why", "you", "your", "up", "down", "over", "under", "using", "via",
    "based", "towards", "toward", "without", "within", "during",
})


class CommunityPostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_by_platform_id(self, data: dict) -> CommunityPost:
        platform = data.get("platform", "")
        external_id = data.get("external_id", "")
        result = await self.session.execute(
            select(CommunityPost).where(
                and_(
                    CommunityPost.platform == platform,
                    CommunityPost.external_id == external_id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        obj = CommunityPost(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_posts(
        self,
        skip: int = 0,
        limit: int = 20,
        platform: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        sort_by: str = "score",
        sort_order: str = "desc",
    ) -> tuple[list[CommunityPost], int]:
        query = select(CommunityPost)
        count_query = select(func.count()).select_from(CommunityPost)

        filters = []
        if platform:
            filters.append(CommunityPost.platform == platform)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    CommunityPost.title.ilike(pattern),
                    CommunityPost.body.ilike(pattern),
                )
            )
        if tag:
            filters.append(CommunityPost.tags.any(tag))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        sort_column = getattr(CommunityPost, sort_by, CommunityPost.score)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        posts = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return posts, total

    async def get_stats(self, platform: str | None = None) -> dict:
        base_filter = []
        if platform:
            base_filter.append(CommunityPost.platform == platform)

        summary_q = select(
            func.count().label("total_posts"),
            func.coalesce(func.avg(CommunityPost.score), 0).label("avg_score"),
        )
        if base_filter:
            summary_q = summary_q.where(and_(*base_filter))
        summary_result = await self.session.execute(summary_q)
        summary = summary_result.one()

        platform_q = (
            select(CommunityPost.platform, func.count().label("cnt"))
            .group_by(CommunityPost.platform)
            .order_by(func.count().desc())
        )
        platform_result = await self.session.execute(platform_q)
        platform_counts = {row.platform: row.cnt for row in platform_result.all()}

        return {
            "total_posts": summary.total_posts or 0,
            "avg_score": round(float(summary.avg_score or 0), 1),
            "platform_counts": platform_counts,
        }

    async def get_platforms(self) -> list[str]:
        result = await self.session.execute(
            select(CommunityPost.platform).distinct().order_by(CommunityPost.platform)
        )
        return list(result.scalars().all())

    async def get_top_tags(self, platform: str | None = None, limit: int = 20) -> list[dict]:
        query = select(CommunityPost.tags).where(CommunityPost.tags.isnot(None))
        if platform:
            query = query.where(CommunityPost.platform == platform)
        query = query.limit(500)

        result = await self.session.execute(query)
        tag_counter: Counter[str] = Counter()
        for (tags,) in result.all():
            if tags:
                for t in tags:
                    tag_counter[t] += 1

        return [{"tag": t, "count": c} for t, c in tag_counter.most_common(limit)]

    async def get_keyword_trends(self, platform: str | None = None, limit: int = 15) -> list[dict]:
        query = select(CommunityPost.title).where(CommunityPost.title.isnot(None))
        if platform:
            query = query.where(CommunityPost.platform == platform)
        query = query.order_by(CommunityPost.published_at.desc()).limit(500)

        result = await self.session.execute(query)
        word_counter: Counter[str] = Counter()
        for (title,) in result.all():
            if title:
                words = re.findall(r"[a-zA-Z]{3,}", title.lower())
                for w in words:
                    if w not in STOPWORDS:
                        word_counter[w] += 1

        return [{"keyword": kw, "count": cnt} for kw, cnt in word_counter.most_common(limit)]
