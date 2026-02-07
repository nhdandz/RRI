import uuid
from datetime import date, timedelta

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.paper import Paper


class PaperRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, paper_id: uuid.UUID) -> Paper | None:
        result = await self.session.execute(select(Paper).where(Paper.id == paper_id))
        return result.scalar_one_or_none()

    async def get_by_arxiv_id(self, arxiv_id: str) -> Paper | None:
        result = await self.session.execute(
            select(Paper).where(Paper.arxiv_id == arxiv_id)
        )
        return result.scalar_one_or_none()

    def _build_filters(
        self,
        category: str | None = None,
        topic: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        has_code: bool | None = None,
        is_vietnamese: bool | None = None,
        search: str | None = None,
        source: str | None = None,
    ) -> list:
        filters = []
        if category:
            cats = [c.strip() for c in category.split(",") if c.strip()]
            if len(cats) == 1:
                filters.append(Paper.categories.any(cats[0]))
            elif len(cats) > 1:
                filters.append(or_(*(Paper.categories.any(c) for c in cats)))
        if topic:
            topics = [t.strip() for t in topic.split(",") if t.strip()]
            if len(topics) == 1:
                filters.append(Paper.topics.any(topics[0]))
            elif len(topics) > 1:
                filters.append(or_(*(Paper.topics.any(t) for t in topics)))
        if date_from:
            filters.append(Paper.published_date >= date_from)
        if date_to:
            filters.append(Paper.published_date <= date_to)
        if is_vietnamese is not None:
            filters.append(Paper.is_vietnamese == is_vietnamese)
        if has_code is not None:
            filters.append(Paper.is_relevant == has_code)
        if source:
            filters.append(Paper.source == source)
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Paper.title.ilike(term),
                    Paper.abstract.ilike(term),
                    Paper.arxiv_id.ilike(term),
                )
            )
        return filters

    async def list_papers(
        self,
        skip: int = 0,
        limit: int = 20,
        category: str | None = None,
        topic: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        has_code: bool | None = None,
        is_vietnamese: bool | None = None,
        search: str | None = None,
        source: str | None = None,
        sort_by: str = "published_date",
        sort_order: str = "desc",
    ) -> tuple[list[Paper], int]:
        filters = self._build_filters(
            category=category, topic=topic, date_from=date_from,
            date_to=date_to, has_code=has_code, is_vietnamese=is_vietnamese,
            search=search, source=source,
        )

        query = select(Paper)
        count_query = select(func.count()).select_from(Paper)

        if filters:
            where = and_(*filters)
            query = query.where(where)
            count_query = count_query.where(where)

        sort_column = getattr(Paper, sort_by, Paper.published_date)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        papers = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return papers, total

    async def get_stats(
        self,
        category: str | None = None,
        topic: str | None = None,
        search: str | None = None,
        source: str | None = None,
    ) -> dict:
        filters = self._build_filters(category=category, topic=topic, search=search, source=source)
        where_clause = and_(*filters) if filters else True

        thirty_days_ago = date.today() - timedelta(days=30)

        # Summary
        summary_q = select(
            func.count().label("total_papers"),
            func.coalesce(func.sum(Paper.citation_count), 0).label("total_citations"),
            func.coalesce(func.avg(Paper.citation_count), 0).label("avg_citations"),
            func.sum(case((Paper.published_date >= thirty_days_ago, 1), else_=0)).label("recent_papers"),
        ).where(where_clause)
        summary = (await self.session.execute(summary_q)).one()

        # Category distribution (unnest ARRAY)
        cat_unnest = func.unnest(Paper.categories).label("category")
        cat_subq = (
            select(Paper.id, cat_unnest)
            .where(where_clause)
            .where(Paper.categories.isnot(None))
            .subquery()
        )
        cat_q = (
            select(cat_subq.c.category, func.count().label("cnt"))
            .group_by(cat_subq.c.category)
            .order_by(func.count().desc())
        )
        cat_result = await self.session.execute(cat_q)
        category_distribution = {row.category: row.cnt for row in cat_result.all()}

        # Source distribution
        source_q = (
            select(Paper.source, func.count().label("cnt"))
            .where(where_clause)
            .group_by(Paper.source)
            .order_by(func.count().desc())
        )
        source_result = await self.session.execute(source_q)
        source_distribution = {row.source: row.cnt for row in source_result.all()}

        # Year distribution
        year_expr = func.extract("year", Paper.published_date).label("year")
        year_q = (
            select(year_expr, func.count().label("cnt"))
            .where(where_clause)
            .where(Paper.published_date.isnot(None))
            .group_by(year_expr)
            .order_by(year_expr.desc())
        )
        year_result = await self.session.execute(year_q)
        year_distribution = {str(int(row.year)): row.cnt for row in year_result.all() if row.year}

        return {
            "total_papers": summary.total_papers or 0,
            "total_citations": int(summary.total_citations or 0),
            "avg_citations": round(float(summary.avg_citations or 0), 1),
            "recent_papers": int(summary.recent_papers or 0),
            "category_distribution": category_distribution,
            "source_distribution": source_distribution,
            "year_distribution": year_distribution,
        }

    async def create(self, paper: Paper) -> Paper:
        self.session.add(paper)
        await self.session.flush()
        return paper

    async def upsert_by_arxiv_id(self, paper_data: dict) -> Paper:
        existing = await self.get_by_arxiv_id(paper_data.get("arxiv_id", ""))
        if existing:
            for key, value in paper_data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        paper = Paper(**paper_data)
        self.session.add(paper)
        await self.session.flush()
        return paper

    async def get_by_s2_id(self, s2_id: str) -> Paper | None:
        result = await self.session.execute(
            select(Paper).where(Paper.semantic_scholar_id == s2_id)
        )
        return result.scalar_one_or_none()

    async def _get_by_doi(self, doi: str) -> Paper | None:
        result = await self.session.execute(
            select(Paper).where(Paper.doi == doi)
        )
        return result.scalar_one_or_none()

    async def upsert_by_s2_id(self, paper_data: dict) -> Paper | None:
        arxiv_id = paper_data.get("arxiv_id")
        s2_id = paper_data.get("semantic_scholar_id", "")
        doi = paper_data.get("doi")

        existing = None
        if arxiv_id:
            existing = await self.get_by_arxiv_id(arxiv_id)
        if not existing and s2_id:
            existing = await self.get_by_s2_id(s2_id)
        if not existing and doi:
            existing = await self._get_by_doi(doi)

        if existing:
            for key, value in paper_data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        try:
            paper = Paper(**paper_data)
            self.session.add(paper)
            await self.session.flush()
            return paper
        except Exception:
            await self.session.rollback()
            return None

    async def get_unprocessed(self, limit: int = 100) -> list[Paper]:
        result = await self.session.execute(
            select(Paper)
            .where(Paper.is_processed == False)  # noqa: E712
            .order_by(Paper.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_processed(self, paper_id: uuid.UUID) -> None:
        paper = await self.get_by_id(paper_id)
        if paper:
            paper.is_processed = True
            await self.session.flush()
