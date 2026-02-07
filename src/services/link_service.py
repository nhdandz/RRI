"""Paper-Code link service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.link import PaperRepoLink


class LinkService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_links_for_paper(self, paper_id: uuid.UUID) -> list[PaperRepoLink]:
        result = await self.session.execute(
            select(PaperRepoLink).where(PaperRepoLink.paper_id == paper_id)
        )
        return list(result.scalars().all())

    async def get_links_for_repo(self, repo_id: uuid.UUID) -> list[PaperRepoLink]:
        result = await self.session.execute(
            select(PaperRepoLink).where(PaperRepoLink.repo_id == repo_id)
        )
        return list(result.scalars().all())

    async def create_link(
        self,
        paper_id: uuid.UUID,
        repo_id: uuid.UUID,
        link_type: str,
        confidence_score: float,
        evidence: dict | None = None,
        discovered_via: str | None = None,
    ) -> PaperRepoLink:
        link = PaperRepoLink(
            paper_id=paper_id,
            repo_id=repo_id,
            link_type=link_type,
            confidence_score=confidence_score,
            evidence=evidence or {},
            discovered_via=discovered_via,
        )
        self.session.add(link)
        await self.session.flush()
        return link
