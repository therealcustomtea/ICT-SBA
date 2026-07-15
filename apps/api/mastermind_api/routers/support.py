from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, get_current_user
from ..database import get_session
from ..models import SupportRequest
from ..rate_limit import RateLimiter
from ..schemas import SupportRequestCreate, SupportRequestResponse
from ..services import ensure_profile

router = APIRouter(prefix="/v1/support", tags=["support"])


@router.post("", response_model=SupportRequestResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_support_request_route(
    payload: SupportRequestCreate,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SupportRequestResponse:
    await ensure_profile(session, principal)
    limiter: RateLimiter = request.app.state.rate_limiter
    subject_key = hashlib.sha256(f"support:{principal.user_id}".encode()).hexdigest()
    # A support request costs twelve ordinary request units, limiting automated abuse
    # without retaining an IP address or other tracking identifier.
    await limiter.check(subject_key, weight=12)
    support_request = SupportRequest(
        user_id=principal.user_id,
        topic=payload.topic,
        reply_email=payload.reply_email,
        message=payload.message,
    )
    session.add(support_request)
    await session.commit()
    return SupportRequestResponse(id=support_request.id, received=True)
