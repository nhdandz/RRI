import uuid

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.repository import Repository


class GitHubRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, repo_id: uuid.UUID) -> Repository | None:
        result = await self.session.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_full_name(self, full_name: str) -> Repository | None:
        result = await self.session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        return result.scalar_one_or_none()

    async def list_repos(
        self,
        skip: int = 0,
        limit: int = 20,
        language: str | None = None,
        topic: str | None = None,
        min_stars: int | None = None,
        search: str | None = None,
        sort_by: str = "stars_count",
        sort_order: str = "desc",
    ) -> tuple[list[Repository], int]:
        query = select(Repository)
        count_query = select(func.count()).select_from(Repository)

        filters = self._build_filters(language, topic, min_stars, search)
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        sort_column = getattr(Repository, sort_by, Repository.stars_count)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        repos = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return repos, total

    async def upsert_by_full_name(self, repo_data: dict) -> Repository:
        existing = await self.get_by_full_name(repo_data.get("full_name", ""))
        if existing:
            for key, value in repo_data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        repo = Repository(**repo_data)
        self.session.add(repo)
        await self.session.flush()
        return repo

    async def list_all_full_names(self) -> list[str]:
        """Return full_name of all repos (lightweight query for update task)."""
        result = await self.session.execute(
            select(Repository.full_name).order_by(Repository.stars_count.desc())
        )
        return list(result.scalars().all())

    def _build_filters(
        self,
        language: str | None = None,
        topic: str | None = None,
        min_stars: int | None = None,
        search: str | None = None,
    ) -> list:
        filters = []
        if language:
            filters.append(Repository.primary_language == language)
        if topic:
            topics = [t.strip() for t in topic.split(",") if t.strip()]
            if len(topics) == 1:
                filters.append(Repository.topics.any(topics[0]))
            elif len(topics) > 1:
                filters.append(or_(*(Repository.topics.any(t) for t in topics)))
        if min_stars:
            filters.append(Repository.stars_count >= min_stars)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Repository.full_name.ilike(pattern),
                    Repository.description.ilike(pattern),
                )
            )
        return filters

    async def get_stats(
        self,
        language: str | None = None,
        topic: str | None = None,
        min_stars: int | None = None,
        search: str | None = None,
    ) -> dict:
        filters = self._build_filters(language, topic, min_stars, search)
        where_clause = and_(*filters) if filters else True

        # Summary stats
        summary_q = select(
            func.count().label("total_repos"),
            func.coalesce(func.sum(Repository.stars_count), 0).label("total_stars"),
            func.coalesce(func.avg(Repository.stars_count), 0).label("avg_stars"),
            func.sum(case((Repository.commit_count_30d > 0, 1), else_=0)).label("active_repos"),
        ).where(where_clause)
        summary_result = await self.session.execute(summary_q)
        summary = summary_result.one()

        # Language distribution
        lang_q = (
            select(
                Repository.primary_language,
                func.count().label("cnt"),
            )
            .where(where_clause)
            .where(Repository.primary_language.isnot(None))
            .group_by(Repository.primary_language)
            .order_by(func.count().desc())
        )
        lang_result = await self.session.execute(lang_q)
        language_distribution = {row.primary_language: row.cnt for row in lang_result.all()}

        # Topic distribution (unnest ARRAY, filter to known topics only)
        from src.core.constants import KNOWN_TOPICS

        topic_unnest = func.unnest(Repository.topics).label("topic")
        topic_subq = (
            select(Repository.id, topic_unnest)
            .where(where_clause)
            .where(Repository.topics.isnot(None))
            .subquery()
        )
        topic_q = (
            select(
                topic_subq.c.topic,
                func.count().label("cnt"),
            )
            .where(topic_subq.c.topic.in_(KNOWN_TOPICS))
            .group_by(topic_subq.c.topic)
            .order_by(func.count().desc())
        )
        topic_result = await self.session.execute(topic_q)
        topic_distribution = {row.topic: row.cnt for row in topic_result.all()}

        return {
            "total_repos": summary.total_repos or 0,
            "total_stars": int(summary.total_stars or 0),
            "avg_stars": round(float(summary.avg_stars or 0), 1),
            "active_repos": int(summary.active_repos or 0),
            "language_distribution": language_distribution,
            "topic_distribution": topic_distribution,
        }

    async def get_unprocessed(self, limit: int = 100) -> list[Repository]:
        result = await self.session.execute(
            select(Repository)
            .where(Repository.is_processed == False)  # noqa: E712
            .order_by(Repository.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
