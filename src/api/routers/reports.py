import uuid
from datetime import date

from fastapi import APIRouter, Query, Response

from src.api.schemas.report import (
    ReportGenerationRequest,
    ReportGenerationResponse,
    WeeklyReportResponse,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    week: date | None = None,
    topics: list[str] | None = Query(None),
):
    # Default to current week
    report_date = week or date.today()

    return WeeklyReportResponse(
        period_start=report_date,
        period_end=report_date,
        new_papers_count=0,
        new_repos_count=0,
        highlights=[],
        trending_topics=[],
        report_content="No report generated yet. Run the weekly report job first.",
    )


@router.post("/generate", response_model=ReportGenerationResponse)
async def generate_report(request: ReportGenerationRequest):
    report_id = str(uuid.uuid4())

    return ReportGenerationResponse(
        report_id=report_id,
        status="generating",
        estimated_time_seconds=30,
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("markdown"),
):
    content = f"# Report {report_id}\n\nReport generation in progress..."

    media_type = "text/markdown" if format == "markdown" else "application/pdf"
    filename = f"report_{report_id}.{'md' if format == 'markdown' else 'pdf'}"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
