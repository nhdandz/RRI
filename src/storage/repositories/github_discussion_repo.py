from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.github_discussion import GitHubDiscussion


class GitHubDiscussionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_by_discussion_id(self, data: dict) -> GitHubDiscussion:
        discussion_id = data.get("discussion_id", "")
        result = await self.session.execute(
            select(GitHubDiscussion).where(
                GitHubDiscussion.discussion_id == discussion_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        obj = GitHubDiscussion(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_discussions(
        self,
        skip: int = 0,
        limit: int = 20,
        repo: str | None = None,
        category: str | None = None,
        search: str | None = None,
        sort_by: str = "upvotes",
        sort_order: str = "desc",
    ) -> tuple[list[GitHubDiscussion], int]:
        query = select(GitHubDiscussion)
        count_query = select(func.count()).select_from(GitHubDiscussion)

        filters = []
        if repo:
            filters.append(GitHubDiscussion.repo_full_name == repo)
        if category:
            filters.append(GitHubDiscussion.category == category)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    GitHubDiscussion.title.ilike(pattern),
                    GitHubDiscussion.body.ilike(pattern),
                )
            )

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        sort_column = getattr(GitHubDiscussion, sort_by, GitHubDiscussion.upvotes)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        discussions = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return discussions, total

    async def get_stats(self) -> dict:
        summary_q = select(
            func.count().label("total"),
            func.count(func.distinct(GitHubDiscussion.repo_full_name)).label("repos_count"),
        )
        summary_result = await self.session.execute(summary_q)
        summary = summary_result.one()

        cat_q = (
            select(GitHubDiscussion.category, func.count().label("cnt"))
            .where(GitHubDiscussion.category.isnot(None))
            .group_by(GitHubDiscussion.category)
            .order_by(func.count().desc())
        )
        cat_result = await self.session.execute(cat_q)
        category_distribution = {row.category: row.cnt for row in cat_result.all()}

        return {
            "total": summary.total or 0,
            "repos_count": summary.repos_count or 0,
            "category_distribution": category_distribution,
        }

    async def get_categories(self) -> list[str]:
        result = await self.session.execute(
            select(GitHubDiscussion.category)
            .where(GitHubDiscussion.category.isnot(None))
            .distinct()
            .order_by(GitHubDiscussion.category)
        )
        return list(result.scalars().all())

    async def get_repos(self) -> list[str]:
        result = await self.session.execute(
            select(GitHubDiscussion.repo_full_name)
            .distinct()
            .order_by(GitHubDiscussion.repo_full_name)
        )
        return list(result.scalars().all())
