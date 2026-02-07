"""Reporting tasks for generating weekly digests and alerts."""

import asyncio
from datetime import date, timedelta

from src.core.config import get_settings
from src.core.logging import get_logger
from src.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="src.workers.tasks.reporting.generate_weekly_report")
def generate_weekly_report():
    """Generate weekly digest report."""
    _run_async(_generate_report())


async def _generate_report():
    from src.llm.ollama_client import OllamaClient
    from src.llm.prompts.analysis import WEEKLY_REPORT_PROMPT
    from src.storage.database import create_async_session_factory
    from src.storage.repositories.metrics_repo import MetricsRepository
    from src.storage.repositories.paper_repo import PaperRepository

    async_session_factory = create_async_session_factory()

    settings = get_settings()
    llm = OllamaClient(base_url=settings.LOCAL_LLM_URL, model=settings.LOCAL_LLM_MODEL)

    period_end = date.today()
    period_start = period_end - timedelta(days=7)

    async with async_session_factory() as session:
        paper_repo = PaperRepository(session)
        metrics_repo = MetricsRepository(session)

        # Get papers from this week
        papers, paper_count = await paper_repo.list_papers(
            date_from=period_start,
            date_to=period_end,
            limit=100,
        )

        # Build summaries
        papers_summary = "\n".join(
            f"- {p.title} [{', '.join(p.categories or [])}]"
            for p in papers[:20]
        )

        # Get trending
        trending = await metrics_repo.get_trending(limit=10)
        repos_summary = "\n".join(
            f"- Score: {t.total_score:.2f} (Category: {t.category or 'unknown'})"
            for t in trending
        )

        # Generate report with LLM
        prompt = WEEKLY_REPORT_PROMPT.format(
            period_start=period_start,
            period_end=period_end,
            paper_count=paper_count,
            papers_summary=papers_summary or "No new papers this week.",
            repo_count=len(trending),
            repos_summary=repos_summary or "No trending repos this week.",
            changes_summary="No notable changes detected.",
        )

        report_content = await llm.generate(
            prompt, max_tokens=2000, temperature=0.5
        )

        logger.info(
            "Weekly report generated",
            papers=paper_count,
            period=f"{period_start} to {period_end}",
        )

        return report_content


@celery_app.task(name="src.workers.tasks.reporting.send_alerts")
def send_alerts():
    """Send pending alerts to subscribers."""
    _run_async(_send_pending_alerts())


async def _send_pending_alerts():
    from sqlalchemy import select

    from src.storage.database import create_async_session_factory
    from src.storage.models.alert import Alert

    async_session_factory = create_async_session_factory()
    async with async_session_factory() as session:
        result = await session.execute(
            select(Alert).where(Alert.is_sent == False).limit(100)  # noqa: E712
        )
        alerts = result.scalars().all()

        for alert in alerts:
            try:
                # Here you would integrate with email/Slack/Telegram
                logger.info("Would send alert", title=alert.title, type=alert.alert_type)
                alert.is_sent = True
            except Exception as e:
                logger.error("Failed to send alert", error=str(e))

        await session.commit()

    logger.info("Alert sending completed", count=len(alerts))
