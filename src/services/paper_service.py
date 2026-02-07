"""Paper business logic service."""

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.paper import Paper
from src.storage.repositories.paper_repo import PaperRepository


class PaperService:
    def __init__(self, session: AsyncSession):
        self.repo = PaperRepository(session)

    async def list_papers(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: dict | None = None,
        sort_by: str = "published_date",
        sort_order: str = "desc",
    ) -> tuple[list[Paper], int]:
        f = filters or {}
        return await self.repo.list_papers(
            skip=skip,
            limit=limit,
            category=f.get("category"),
            topic=f.get("topic"),
            date_from=f.get("date_from"),
            date_to=f.get("date_to"),
            has_code=f.get("has_code"),
            is_vietnamese=f.get("is_vietnamese"),
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_paper(self, paper_id: uuid.UUID) -> Paper | None:
        return await self.repo.get_by_id(paper_id)

    async def get_paper_by_arxiv(self, arxiv_id: str) -> Paper | None:
        return await self.repo.get_by_arxiv_id(arxiv_id)
