from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, get_current_user
from ..config import Settings, get_settings
from ..crypto import SecretCipher
from ..database import get_session
from ..dependencies import get_cipher
from ..errors import APIError
from ..features import feature_enabled
from ..models import FriendChallenge, GameSession
from ..rate_limit import enforce_action_limit
from ..schemas import (
    ChallengeResponse,
    ChallengeResultItem,
    ChallengeResultsResponse,
    CreateChallengeRequest,
    GameConfigSchema,
    GameResponse,
    OwnedChallengeItem,
    PaginatedOwnedChallenges,
    StartGameRequest,
)
from ..services import (
    challenge_response,
    create_challenge,
    game_response,
    load_challenge,
    start_challenge,
    utcnow,
)

router = APIRouter(prefix="/v1/challenges", tags=["friend challenges"])


async def require_challenges(session: AsyncSession, settings: Settings) -> None:
    if not await feature_enabled(session, settings, "friend_challenges"):
        raise APIError(503, "FEATURE_DISABLED", "Friend challenges are temporarily unavailable.")


@router.get("/{challenge_id}/results", response_model=ChallengeResultsResponse)
async def challenge_results_route(
    challenge_id: uuid.UUID,
    page: int = 1,
    page_size: int = 25,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ChallengeResultsResponse:
    await require_challenges(session, settings)
    if page < 1 or not 1 <= page_size <= 100:
        raise APIError(422, "INVALID_PAGE", "Use a positive page and a page size up to 100.")
    challenge = await session.scalar(
        select(FriendChallenge).where(
            FriendChallenge.id == challenge_id,
            FriendChallenge.creator_id == principal.user_id,
        )
    )
    if challenge is None:
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    base = select(GameSession).where(
        GameSession.friend_challenge_id == challenge.id,
        GameSession.completed_at.is_not(None),
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    aggregate = await session.execute(
        select(
            func.sum(case((GameSession.status == "won", 1), else_=0)),
            func.avg(GameSession.attempts_used),
        ).where(
            GameSession.friend_challenge_id == challenge.id,
            GameSession.completed_at.is_not(None),
        )
    )
    wins, average = aggregate.one()
    results = (
        await session.scalars(
            base.order_by(
                func.coalesce(GameSession.final_score, 0).desc(),
                GameSession.attempts_used.asc(),
                GameSession.elapsed_seconds.asc().nulls_last(),
                GameSession.completed_at.asc(),
                GameSession.public_id.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    all_scores = list(
        await session.scalars(
            select(GameSession.final_score).where(
                GameSession.friend_challenge_id == challenge.id,
                GameSession.completed_at.is_not(None),
            )
        )
    )
    distribution = {"zero": 0, "1-999": 0, "1000-1499": 0, "1500+": 0}
    for score in all_scores:
        value = score or 0
        bucket = (
            "zero"
            if value == 0
            else "1-999"
            if value < 1000
            else "1000-1499"
            if value < 1500
            else "1500+"
        )
        distribution[bucket] += 1
    return ChallengeResultsResponse(
        completed_count=total,
        win_rate=round((wins or 0) / total * 100, 1) if total else 0.0,
        average_attempts=round(float(average), 2) if average is not None else None,
        score_distribution=distribution,
        items=[
            ChallengeResultItem(
                rank=(page - 1) * page_size + index,
                player_label=f"Breaker {game.public_id[:6].upper()}",
                result=game.status,
                attempts_used=game.attempts_used,
                max_attempts=game.maximum_attempts,
                score=game.final_score or 0,
                elapsed_seconds=game.elapsed_seconds,
                completed_at=game.completed_at,
            )
            for index, game in enumerate(results, start=1)
            if game.completed_at is not None
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge_route(
    payload: CreateChallengeRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
    settings: Settings = Depends(get_settings),
) -> ChallengeResponse:
    await require_challenges(session, settings)
    await enforce_action_limit(
        request,
        action="challenge.create",
        subject=principal.user_id,
        weight=10,
        integrity_required=True,
    )
    challenge, share_code = await create_challenge(session, principal, payload, cipher, settings)
    return await challenge_response(session, challenge, principal, share_code)


@router.get("/mine", response_model=PaginatedOwnedChallenges)
async def owned_challenges_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> PaginatedOwnedChallenges:
    await require_challenges(session, settings)
    completed_count = (
        select(func.count(GameSession.id))
        .where(
            GameSession.friend_challenge_id == FriendChallenge.id,
            GameSession.completed_at.is_not(None),
        )
        .correlate(FriendChallenge)
        .scalar_subquery()
    )
    base = select(FriendChallenge, completed_count.label("completed_count")).where(
        FriendChallenge.creator_id == principal.user_id
    )
    total = (
        await session.scalar(
            select(func.count()).select_from(
                select(FriendChallenge.id)
                .where(FriendChallenge.creator_id == principal.user_id)
                .subquery()
            )
        )
        or 0
    )
    rows = (
        await session.execute(
            base.order_by(FriendChallenge.created_at.desc(), FriendChallenge.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return PaginatedOwnedChallenges(
        items=[
            OwnedChallengeItem(
                id=challenge.id,
                title=challenge.title,
                show_creator_name=challenge.show_creator_name,
                config=GameConfigSchema.model_validate(challenge.config),
                revoked=challenge.revoked_at is not None,
                expires_at=challenge.expires_at,
                completed_count=count,
                created_at=challenge.created_at,
            )
            for challenge, count in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{share_code}", response_model=ChallengeResponse)
async def get_challenge_route(
    share_code: str,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ChallengeResponse:
    await require_challenges(session, settings)
    await enforce_action_limit(
        request,
        action="challenge.lookup",
        subject=principal.user_id,
        resource=share_code,
        weight=2,
        integrity_required=True,
    )
    challenge = await load_challenge(session, share_code, settings)
    return await challenge_response(session, challenge, principal, share_code)


@router.post("/{share_code}/start", response_model=GameResponse)
async def start_challenge_route(
    share_code: str,
    request: Request,
    payload: StartGameRequest | None = None,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
    settings: Settings = Depends(get_settings),
) -> GameResponse:
    await require_challenges(session, settings)
    await enforce_action_limit(
        request,
        action="challenge.start",
        subject=principal.user_id,
        resource=share_code,
        weight=6,
        integrity_required=True,
    )
    challenge = await load_challenge(session, share_code, settings)
    game = await start_challenge(
        session,
        principal,
        challenge,
        cipher,
        practice=bool(payload and payload.practice),
    )
    return game_response(game, cipher)


@router.delete(
    "/{challenge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def revoke_challenge_route(
    challenge_id: uuid.UUID,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> None:
    await require_challenges(session, settings)
    await enforce_action_limit(
        request,
        action="challenge.revoke",
        subject=principal.user_id,
        resource=challenge_id,
        weight=8,
        integrity_required=True,
    )
    challenge = await session.scalar(
        select(FriendChallenge).where(
            FriendChallenge.id == challenge_id,
            FriendChallenge.creator_id == principal.user_id,
        )
    )
    if challenge is None:
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    if challenge.revoked_at is None:
        challenge.revoked_at = utcnow()
        await session.commit()
