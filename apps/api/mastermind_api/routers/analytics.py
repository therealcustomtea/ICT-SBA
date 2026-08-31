# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `structlog` so the module can use that dependency.
import structlog

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, status

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, get_current_user

# Imports selected names from `..config` for use in this module.
from ..config import Settings, get_settings

# Imports selected names from `..database` for use in this module.
from ..database import MongoSession, document_to_bson, get_session

# Imports selected names from `..errors` for use in this module.
from ..errors import APIError

# Imports selected names from `..features` for use in this module.
from ..features import feature_enabled

# Imports selected names from `..models` for use in this module.
from ..models import ProductEvent

# Imports selected names from `..retention` for use in this module.
from ..retention import PRODUCT_EVENT_RETENTION

# Imports selected names from `..schemas` for use in this module.
from ..schemas import AnalyticsEventRequest, AnalyticsEventResponse

# Imports selected names from `..services` for use in this module.
from ..services import ensure_profile, utcnow

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/analytics", tags=["analytics"])

# Computes and stores `EVENT_FIELDS` for subsequent operations.
EVENT_FIELDS = (
    # Supplies this item to the surrounding call or collection.
    "locale",
    # Supplies this item to the surrounding call or collection.
    "mode",
    # Supplies this item to the surrounding call or collection.
    "difficulty",
    # Supplies this item to the surrounding call or collection.
    "result",
    # Supplies this item to the surrounding call or collection.
    "attempts_used",
    # Supplies this item to the surrounding call or collection.
    "ranked",
    # Supplies this item to the surrounding call or collection.
    "score_band",
    # Supplies this item to the surrounding call or collection.
    "daily_challenge_id",
    # Supplies this item to the surrounding call or collection.
    "official",
    # Supplies this item to the surrounding call or collection.
    "expiry_band",
    # Supplies this item to the surrounding call or collection.
    "room_state",
    # Supplies this item to the surrounding call or collection.
    "reconnect",
    # Supplies this item to the surrounding call or collection.
    "tie",
    # Supplies this item to the surrounding call or collection.
    "validation_category",
    # Supplies this item to the surrounding call or collection.
    "surface",
    # Supplies this item to the surrounding call or collection.
    "recovered",
    # Supplies this item to the surrounding call or collection.
    "previous_anonymous",
    # Closes the multiline call, declaration, or collection started above.
)


# Applies `@router.post(` to configure the declaration immediately below.
@router.post(
    # Supplies this item to the surrounding call or collection.
    "/events",
    # Provides the `response_model` parameter or keyword argument.
    response_model=AnalyticsEventResponse,
    # Provides the `status_code` parameter or keyword argument.
    status_code=status.HTTP_202_ACCEPTED,
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `collect_event_route` callable and its typed interface.
async def collect_event_route(
    # Declares the typed `payload` data field.
    payload: AnalyticsEventRequest,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: MongoSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> AnalyticsEventResponse:
    # Checks this condition before executing the nested branch.
    if not await feature_enabled(session, settings, "analytics"):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "FEATURE_DISABLED", "Product analytics are disabled.")
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `occurred_at` for subsequent operations.
    occurred_at = utcnow()
    # Computes and stores `event_values` for subsequent operations.
    event_values = {
        # Associates the `client_event_id` key with its value.
        "client_event_id": payload.client_event_id,
        # Associates the `event_name` key with its value.
        "event_name": payload.event_name,
        # Associates the `anonymous` key with its value.
        "anonymous": principal.is_anonymous,
        # Associates the `consent_version` key with its value.
        "consent_version": payload.consent_version,
        # Associates the `release` key with its value.
        "release": settings.release[:64],
        # Associates the `occurred_at` key with its value.
        "occurred_at": occurred_at,
        # Associates the `expires_at` key with its value.
        "expires_at": occurred_at + PRODUCT_EVENT_RETENTION,
        # Supplies this item to the surrounding call or collection.
        **{field: getattr(payload, field) for field in EVENT_FIELDS},
        # Closes the multiline call, declaration, or collection started above.
    }
    # Stores `event` because later steps depend on this value.
    event = ProductEvent(**event_values)
    # Performs this required operation before the surrounding flow continues.
    await session.upsert_one(
        # Supplies this required nested value.
        ProductEvent,
        # Supplies this required nested value.
        {"client_event_id": payload.client_event_id},
        # Supplies this required nested value.
        {"$setOnInsert": document_to_bson(event)},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Calls `structlog.get_logger` with the supplied values.
    structlog.get_logger().info(
        # Supplies this item to the surrounding call or collection.
        "product_event_recorded",
        # Provides the `product_event` parameter or keyword argument.
        product_event=payload.event_name,
        # Provides the `anonymous` parameter or keyword argument.
        anonymous=principal.is_anonymous,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return AnalyticsEventResponse(received=True)
