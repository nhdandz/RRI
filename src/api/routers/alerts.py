from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import DbSession
from src.api.schemas.report import AlertResponse, SubscribeRequest, SubscriptionResponse
from src.storage.models.alert import Alert
from src.storage.models.subscription import Subscription

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    db: DbSession,
    alert_type: str | None = None,
    severity: str | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    query = select(Alert).order_by(Alert.created_at.desc()).limit(limit)

    filters = []
    if alert_type:
        filters.append(Alert.alert_type == alert_type)
    if severity:
        filters.append(Alert.severity == severity)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    alerts = result.scalars().all()

    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(request: SubscribeRequest, db: DbSession):
    subscription = Subscription(
        subscriber_id=request.email,
        subscription_type=request.subscription_type,
        target_value=request.target_value,
        channels=request.channels,
        frequency=request.frequency,
    )
    db.add(subscription)
    await db.flush()
    return SubscriptionResponse.model_validate(subscription)
