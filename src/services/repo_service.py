"""Repository business logic service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.repository import Repository
from src.storage.repositories.github_repo import GitHubRepository


class RepoService:
    def __init__(self, session: AsyncSession):
        self.repo = GitHubRepository(session)

    async def list_repos(
        self,
        skip: int = 0,
        limit: int = 20,
        language: str | None = None,
        topic: str | None = None,
        min_stars: int | None = None,
        sort_by: str = "stars_count",
        sort_order: str = "desc",
    ) -> tuple[list[Repository], int]:
        return await self.repo.list_repos(
            skip=skip,
            limit=limit,
            language=language,
            topic=topic,
            min_stars=min_stars,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_repo(self, repo_id: uuid.UUID) -> Repository | None:
        return await self.repo.get_by_id(repo_id)

    async def get_repo_by_name(self, full_name: str) -> Repository | None:
        return await self.repo.get_by_full_name(full_name)
