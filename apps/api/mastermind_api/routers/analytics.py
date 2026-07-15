from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, get_current_user
from ..config import Settings, get_settings
from ..database import get_session
from ..errors import APIError
from ..features import feature_enabled
from ..models import ProductEvent
from ..retention import PRODUCT_EVENT_RETENTION
from ..schemas import AnalyticsEventRequest, AnalyticsEventResponse
from ..services import ensure_profile, utcnow

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])

EVENT_FIELDS = (
    "locale",
    "mode",
    "difficulty",
    "result",
    "attempts_used",
    "ranked",
    "score_band",
    "daily_challenge_id",
    "official",
    "expiry_band",
    "room_state",
    "reconnect",
    "tie",
    "validation_category",
    "surface",
    "recovered",
    "previous_anonymous",
)


@router.post(
    "/events",
    response_model=AnalyticsEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def collect_event_route(
    payload: AnalyticsEventRequest,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AnalyticsEventResponse:
    if not await feature_enabled(session, settings, "analytics"):
        raise APIError(503, "FEATURE_DISABLED", "Product analytics are disabled.")
    await ensure_profile(session, principal)
    occurred_at = utcnow()
    event_values = {
        "client_event_id": payload.client_event_id,
        "event_name": payload.event_name,
        "anonymous": principal.is_anonymous,
        "consent_version": payload.consent_version,
        "release": settings.release[:64],
        "occurred_at": occurred_at,
        "expires_at": occurred_at + PRODUCT_EVENT_RETENTION,
        **{field: getattr(payload, field) for field in EVENT_FIELDS},
    }
    dialect_name = session.bind.dialect.name if session.bind is not None else ""
    if dialect_name == "postgresql":
        await session.execute(
            postgresql_insert(ProductEvent)
            .values(**event_values)
            .on_conflict_do_nothing(index_elements=[ProductEvent.client_event_id])
        )
    elif dialect_name == "sqlite":
        await session.execute(
            sqlite_insert(ProductEvent)
            .values(**event_values)
            .on_conflict_do_nothing(index_elements=[ProductEvent.client_event_id])
        )
    else:
        raise APIError(503, "ANALYTICS_UNAVAILABLE", "Product analytics are unavailable.")
    await session.commit()
    structlog.get_logger().info(
        "product_event_recorded",
        product_event=payload.event_name,
        anonymous=principal.is_anonymous,
    )
    return AnalyticsEventResponse(received=True)
