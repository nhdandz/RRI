import uuid
from datetime import date, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models.metrics import MetricsHistory, TrendingScore


class MetricsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_history(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        days: int = 30,
    ) -> list[MetricsHistory]:
        cutoff = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(MetricsHistory)
            .where(
                and_(
                    MetricsHistory.entity_type == entity_type,
                    MetricsHistory.entity_id == entity_id,
                    MetricsHistory.recorded_at >= cutoff,
                )
            )
            .order_by(MetricsHistory.recorded_at.asc())
        )
        return list(result.scalars().all())

    async def record_metrics(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        metrics: dict,
        recorded_at: date | None = None,
    ) -> MetricsHistory:
        record = MetricsHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            metrics=metrics,
            recorded_at=recorded_at or date.today(),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def upsert_daily_snapshot(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        metrics: dict,
    ) -> MetricsHistory:
        """Record or update today's snapshot, and compute velocity fields."""
        today = date.today()

        # Check if today's snapshot already exists
        result = await self.session.execute(
            select(MetricsHistory).where(
                and_(
                    MetricsHistory.entity_type == entity_type,
                    MetricsHistory.entity_id == entity_id,
                    MetricsHistory.recorded_at == today,
                )
            )
        )
        existing = result.scalar_one_or_none()

        # Calculate velocities from historical data
        velocity_1d = await self._calc_velocity(entity_type, entity_id, days=1, current_metrics=metrics)
        velocity_7d = await self._calc_velocity(entity_type, entity_id, days=7, current_metrics=metrics)
        velocity_30d = await self._calc_velocity(entity_type, entity_id, days=30, current_metrics=metrics)

        if existing:
            existing.metrics = metrics
            existing.velocity_1d = velocity_1d
            existing.velocity_7d = velocity_7d
            existing.velocity_30d = velocity_30d
            await self.session.flush()
            return existing

        record = MetricsHistory(
            entity_type=entity_type,
            entity_id=entity_id,
            metrics=metrics,
            recorded_at=today,
            velocity_1d=velocity_1d,
            velocity_7d=velocity_7d,
            velocity_30d=velocity_30d,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def _calc_velocity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        days: int,
        current_metrics: dict,
    ) -> float | None:
        """Calculate star velocity (stars gained per day) over a period."""
        target_date = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(MetricsHistory)
            .where(
                and_(
                    MetricsHistory.entity_type == entity_type,
                    MetricsHistory.entity_id == entity_id,
                    MetricsHistory.recorded_at <= target_date,
                )
            )
            .order_by(MetricsHistory.recorded_at.desc())
            .limit(1)
        )
        old = result.scalar_one_or_none()
        if not old:
            return None

        old_stars = old.metrics.get("stars_count", 0)
        new_stars = current_metrics.get("stars_count", 0)
        actual_days = (date.today() - old.recorded_at).days
        if actual_days == 0:
            return None
        return (new_stars - old_stars) / actual_days

    async def get_trending(
        self,
        entity_type: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[TrendingScore]:
        query = select(TrendingScore).order_by(TrendingScore.total_score.desc())

        filters = []
        if entity_type:
            filters.append(TrendingScore.entity_type == entity_type)
        if category:
            filters.append(TrendingScore.category == category)
        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_trending_score(self, score_data: dict) -> TrendingScore:
        existing = await self.session.execute(
            select(TrendingScore).where(
                and_(
                    TrendingScore.entity_type == score_data["entity_type"],
                    TrendingScore.entity_id == score_data["entity_id"],
                    TrendingScore.period_start == score_data["period_start"],
                )
            )
        )
        existing_score = existing.scalar_one_or_none()

        if existing_score:
            for key, value in score_data.items():
                setattr(existing_score, key, value)
            await self.session.flush()
            return existing_score

        score = TrendingScore(**score_data)
        self.session.add(score)
        await self.session.flush()
        return score
