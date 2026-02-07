"""Trending Score Calculator."""

from dataclasses import dataclass
from datetime import datetime

from src.core.logging import get_logger
from src.storage.repositories.metrics_repo import MetricsRepository

logger = get_logger(__name__)


@dataclass
class TrendingScores:
    activity_score: float
    community_score: float
    academic_score: float
    recency_score: float
    total_score: float


class TrendingCalculator:
    """
    Calculates trending scores for papers and repositories.

    Weights:
    - Activity (40%): Recent commits, issues activity
    - Community (30%): Star/fork velocity
    - Academic (20%): Citation velocity
    - Recency (10%): Time since last update
    """

    W_ACTIVITY = 0.40
    W_COMMUNITY = 0.30
    W_ACADEMIC = 0.20
    W_RECENCY = 0.10

    def __init__(self, metrics_repo: MetricsRepository):
        self.metrics = metrics_repo

    async def calculate_repo_score(
        self,
        repo_id,
        stars_count: int,
        forks_count: int,
        open_issues_count: int,
        commit_count_30d: int,
        last_commit_at: datetime | None,
        citation_count: int = 0,
        period_days: int = 7,
    ) -> TrendingScores:
        history = await self.metrics.get_history(
            entity_type="repository", entity_id=repo_id, days=period_days
        )

        # Activity Score
        activity = 0.0
        if commit_count_30d:
            activity += min(1.0, commit_count_30d / 30) * 0.5
        if open_issues_count > 0:
            activity += min(1.0, open_issues_count / 50) * 0.3
        if last_commit_at:
            days_since = (datetime.utcnow() - last_commit_at).days
            if days_since < 7:
                activity += 0.2
            elif days_since < 30:
                activity += 0.1
        activity = min(1.0, activity)

        # Community Score
        if not history or len(history) < 2:
            community = min(1.0, stars_count / 10000)
        else:
            old_stars = history[-1].metrics.get("stars", stars_count)
            new_stars = stars_count - old_stars
            velocity = new_stars / stars_count if stars_count > 0 else 0.0
            community = min(1.0, velocity * 10)

        # Academic Score
        academic = min(1.0, citation_count / 100) if citation_count else 0.5

        # Recency Score
        recency = self._calculate_recency(last_commit_at)

        total = (
            activity * self.W_ACTIVITY
            + community * self.W_COMMUNITY
            + academic * self.W_ACADEMIC
            + recency * self.W_RECENCY
        )

        return TrendingScores(
            activity_score=activity,
            community_score=community,
            academic_score=academic,
            recency_score=recency,
            total_score=total,
        )

    async def calculate_paper_score(
        self,
        paper_id,
        citation_count: int,
        influential_citation_count: int,
        published_date: datetime | None,
        period_days: int = 30,
    ) -> TrendingScores:
        history = await self.metrics.get_history(
            entity_type="paper", entity_id=paper_id, days=period_days
        )

        activity = 0.5
        community = 0.5

        # Academic Score (citation velocity)
        if not history or len(history) < 2:
            academic = min(1.0, citation_count / 100)
        else:
            old_citations = history[-1].metrics.get("citations", citation_count)
            new_citations = citation_count - old_citations
            velocity_score = min(1.0, new_citations / 10)
            influential_ratio = (
                influential_citation_count / citation_count
                if citation_count > 0
                else 0
            )
            quality_boost = influential_ratio * 0.5
            academic = min(1.0, velocity_score + quality_boost)

        recency = self._calculate_recency(published_date)

        total = (
            activity * self.W_ACTIVITY
            + community * self.W_COMMUNITY
            + academic * self.W_ACADEMIC
            + recency * self.W_RECENCY
        )

        return TrendingScores(
            activity_score=activity,
            community_score=community,
            academic_score=academic,
            recency_score=recency,
            total_score=total,
        )

    def _calculate_recency(self, last_activity: datetime | None) -> float:
        if not last_activity:
            return 0.0
        days_ago = (datetime.utcnow() - last_activity).days
        if days_ago <= 0:
            return 1.0
        elif days_ago <= 7:
            return 1.0 - (days_ago / 14)
        elif days_ago <= 30:
            return 0.5 - ((days_ago - 7) / 46)
        return max(0.0, 0.2 - ((days_ago - 30) / 150))
