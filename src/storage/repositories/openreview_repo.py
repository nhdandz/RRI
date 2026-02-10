import re
from collections import Counter

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.openreview_note import OpenReviewNote

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


class OpenReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_by_note_id(self, data: dict) -> OpenReviewNote:
        note_id = data.get("note_id", "")
        result = await self.session.execute(
            select(OpenReviewNote).where(OpenReviewNote.note_id == note_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        obj = OpenReviewNote(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_notes(
        self,
        skip: int = 0,
        limit: int = 20,
        venue: str | None = None,
        primary_area: str | None = None,
        search: str | None = None,
        min_rating: float | None = None,
        sort_by: str = "average_rating",
        sort_order: str = "desc",
    ) -> tuple[list[OpenReviewNote], int]:
        query = select(OpenReviewNote)
        count_query = select(func.count()).select_from(OpenReviewNote)

        filters = []
        if venue:
            filters.append(OpenReviewNote.venue == venue)
        if primary_area:
            filters.append(OpenReviewNote.primary_area == primary_area)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    OpenReviewNote.title.ilike(pattern),
                    OpenReviewNote.abstract.ilike(pattern),
                )
            )
        if min_rating is not None:
            filters.append(OpenReviewNote.average_rating >= min_rating)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        sort_column = getattr(OpenReviewNote, sort_by, OpenReviewNote.average_rating)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc().nulls_last())
        else:
            query = query.order_by(sort_column.asc().nulls_last())

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        notes = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return notes, total

    async def get_stats(self) -> dict:
        summary_q = select(
            func.count().label("total"),
            func.coalesce(func.avg(OpenReviewNote.average_rating), 0).label("avg_rating"),
        )
        summary_result = await self.session.execute(summary_q)
        summary = summary_result.one()

        # Count reviewed vs unreviewed
        reviewed_q = select(func.count()).select_from(OpenReviewNote).where(
            OpenReviewNote.reviews_fetched == True  # noqa: E712
        )
        reviewed_result = await self.session.execute(reviewed_q)
        reviewed_count = reviewed_result.scalar() or 0

        # Count linked papers
        linked_q = select(func.count()).select_from(OpenReviewNote).where(
            OpenReviewNote.paper_id.isnot(None)
        )
        linked_result = await self.session.execute(linked_q)
        linked_count = linked_result.scalar() or 0

        venue_q = (
            select(OpenReviewNote.venue, func.count().label("cnt"))
            .where(OpenReviewNote.venue.isnot(None))
            .group_by(OpenReviewNote.venue)
            .order_by(func.count().desc())
        )
        venue_result = await self.session.execute(venue_q)
        venue_distribution = {row.venue: row.cnt for row in venue_result.all()}

        # Primary area distribution (top 20)
        area_q = (
            select(OpenReviewNote.primary_area, func.count().label("cnt"))
            .where(OpenReviewNote.primary_area.isnot(None))
            .group_by(OpenReviewNote.primary_area)
            .order_by(func.count().desc())
            .limit(20)
        )
        area_result = await self.session.execute(area_q)
        area_distribution = {row.primary_area: row.cnt for row in area_result.all()}

        return {
            "total": summary.total or 0,
            "avg_rating": round(float(summary.avg_rating or 0), 2),
            "reviewed_count": reviewed_count,
            "linked_count": linked_count,
            "venue_distribution": venue_distribution,
            "area_distribution": area_distribution,
        }

    async def get_venues(self) -> list[str]:
        result = await self.session.execute(
            select(OpenReviewNote.venue)
            .where(OpenReviewNote.venue.isnot(None))
            .distinct()
            .order_by(OpenReviewNote.venue)
        )
        return list(result.scalars().all())

    async def get_primary_areas(self) -> list[str]:
        result = await self.session.execute(
            select(OpenReviewNote.primary_area)
            .where(OpenReviewNote.primary_area.isnot(None))
            .distinct()
            .order_by(OpenReviewNote.primary_area)
        )
        return list(result.scalars().all())

    async def get_keyword_trends(self, limit: int = 15) -> list[dict]:
        query = (
            select(OpenReviewNote.keywords)
            .where(OpenReviewNote.keywords.isnot(None))
            .limit(500)
        )
        result = await self.session.execute(query)
        kw_counter: Counter[str] = Counter()
        for (keywords,) in result.all():
            if keywords:
                for kw in keywords:
                    kw_counter[kw.lower()] += 1

        if not kw_counter:
            # Fallback to title-based keywords
            title_q = (
                select(OpenReviewNote.title)
                .where(OpenReviewNote.title.isnot(None))
                .order_by(OpenReviewNote.published_at.desc())
                .limit(500)
            )
            title_result = await self.session.execute(title_q)
            for (title,) in title_result.all():
                if title:
                    words = re.findall(r"[a-zA-Z]{3,}", title.lower())
                    for w in words:
                        if w not in STOPWORDS:
                            kw_counter[w] += 1

        return [{"keyword": kw, "count": cnt} for kw, cnt in kw_counter.most_common(limit)]
