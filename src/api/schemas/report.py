from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class WeeklyReportResponse(BaseModel):
    period_start: date
    period_end: date
    new_papers_count: int
    new_repos_count: int
    highlights: list[str]
    trending_topics: list[dict]
    report_content: str


class ReportGenerationRequest(BaseModel):
    topic: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    format: str = "markdown"


class ReportGenerationResponse(BaseModel):
    report_id: str
    status: str
    estimated_time_seconds: int = 30


class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    title: str
    description: str | None = None
    severity: str
    entity_type: str | None = None
    created_at: datetime
    is_sent: bool = False

    model_config = {"from_attributes": True}


class SubscribeRequest(BaseModel):
    email: str
    subscription_type: str
    target_value: str
    channels: list[str] = ["email"]
    frequency: str = "daily"


class SubscriptionResponse(BaseModel):
    id: UUID
    subscription_type: str
    target_value: str
    frequency: str
    is_active: bool

    model_config = {"from_attributes": True}
