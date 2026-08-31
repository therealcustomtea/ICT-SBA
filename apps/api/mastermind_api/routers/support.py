# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Request, status

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, get_current_user

# Imports selected names from `..database` for use in this module.
from ..database import MongoSession, get_session

# Imports selected names from `..models` for use in this module.
from ..models import SupportRequest

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import RateLimiter

# Imports selected names from `..schemas` for use in this module.
from ..schemas import SupportRequestCreate, SupportRequestResponse

# Imports selected names from `..services` for use in this module.
from ..services import ensure_profile

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/support", tags=["support"])


# Applies `@router.post("", response_model=SupportRequestResponse,
# status_code=status.HTTP_202_ACCEPTED)` to configure the declaration immediately below.
@router.post("", response_model=SupportRequestResponse, status_code=status.HTTP_202_ACCEPTED)
# Defines the `create_support_request_route` callable and its typed interface.
async def create_support_request_route(
    # Declares the typed `payload` data field.
    payload: SupportRequestCreate,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: MongoSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> SupportRequestResponse:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `limiter` for subsequent operations.
    limiter: RateLimiter = request.app.state.rate_limiter
    # Computes and stores `subject_key` for subsequent operations.
    subject_key = hashlib.sha256(f"support:{principal.user_id}".encode()).hexdigest()
    # A support request costs twelve ordinary request units, limiting automated abuse
    # without retaining an IP address or other tracking identifier.
    # Waits for this asynchronous operation to complete.
    await limiter.check(subject_key, weight=12)
    # Computes and stores `support_request` for subsequent operations.
    support_request = SupportRequest(
        # Provides the `user_id` parameter or keyword argument.
        user_id=principal.user_id,
        # Provides the `topic` parameter or keyword argument.
        topic=payload.topic,
        # Provides the `reply_email` parameter or keyword argument.
        reply_email=payload.reply_email,
        # Provides the `message` parameter or keyword argument.
        message=payload.message,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `session.add` with the supplied values.
    session.add(support_request)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return SupportRequestResponse(id=support_request.id, received=True)
