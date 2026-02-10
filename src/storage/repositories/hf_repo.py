import re
from collections import Counter

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.hf_model import HFModel
from src.storage.models.hf_paper import HFPaper

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


class HFModelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_by_model_id(self, data: dict) -> HFModel:
        model_id = data.get("model_id", "")
        result = await self.session.execute(
            select(HFModel).where(HFModel.model_id == model_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        obj = HFModel(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_models(
        self,
        skip: int = 0,
        limit: int = 20,
        task: str | None = None,
        search: str | None = None,
        sort_by: str = "downloads",
        sort_order: str = "desc",
    ) -> tuple[list[HFModel], int]:
        query = select(HFModel)
        count_query = select(func.count()).select_from(HFModel)

        filters = []
        if task:
            filters.append(HFModel.pipeline_tag == task)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    HFModel.model_id.ilike(pattern),
                    HFModel.author.ilike(pattern),
                )
            )

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        sort_column = getattr(HFModel, sort_by, HFModel.downloads)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        models = list(result.scalars().all())

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        return models, total

    async def get_by_model_id(self, model_id: str) -> HFModel | None:
        result = await self.session.execute(
            select(HFModel).where(HFModel.model_id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_stats(self) -> dict:
        summary_q = select(
            func.count().label("total_models"),
            func.coalesce(func.sum(HFModel.downloads), 0).label("total_downloads"),
            func.coalesce(func.sum(HFModel.likes), 0).label("total_likes"),
        )
        summary_result = await self.session.execute(summary_q)
        summary = summary_result.one()

        pipeline_q = (
            select(
                HFModel.pipeline_tag,
                func.count().label("cnt"),
            )
            .where(HFModel.pipeline_tag.isnot(None))
            .group_by(HFModel.pipeline_tag)
            .order_by(func.count().desc())
        )
        pipeline_result = await self.session.execute(pipeline_q)
        pipeline_distribution = {
            row.pipeline_tag: row.cnt for row in pipeline_result.all()
        }

        return {
            "total_models": summary.total_models or 0,
            "total_downloads": int(summary.total_downloads or 0),
            "total_likes": int(summary.total_likes or 0),
            "pipeline_distribution": pipeline_distribution,
        }

    async def get_pipeline_tags(self) -> list[str]:
        result = await self.session.execute(
            select(HFModel.pipeline_tag)
            .where(HFModel.pipeline_tag.isnot(None))
            .distinct()
            .order_by(HFModel.pipeline_tag)
        )
        return list(result.scalars().all())


class HFPaperRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_by_arxiv_id(self, data: dict) -> HFPaper:
        arxiv_id = data.get("arxiv_id", "")
        result = await self.session.execute(
            select(HFPaper).where(HFPaper.arxiv_id == arxiv_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            await self.session.flush()
            return existing

        obj = HFPaper(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_recent(self, limit: int = 50) -> list[HFPaper]:
        # Get latest collected_date
        date_q = select(func.max(HFPaper.collected_date))
        date_result = await self.session.execute(date_q)
        latest_date = date_result.scalar()

        if not latest_date:
            return []

        result = await self.session.execute(
            select(HFPaper)
            .where(HFPaper.collected_date == latest_date)
            .order_by(HFPaper.upvotes.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_keyword_trends(self, limit: int = 15) -> list[dict]:
        papers = await self.list_recent(limit=200)
        word_counter: Counter[str] = Counter()
        for paper in papers:
            words = re.findall(r"[a-zA-Z]{3,}", paper.title.lower())
            for w in words:
                if w not in STOPWORDS:
                    word_counter[w] += 1

        return [
            {"keyword": kw, "count": cnt}
            for kw, cnt in word_counter.most_common(limit)
        ]
