from __future__ import annotations

import hashlib
import time as monotonic_time
from contextlib import suppress
from datetime import UTC, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query, Request
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, get_current_user
from ..cache import leaderboard_cache_version
from ..config import Settings, get_settings
from ..crypto import SecretCipher
from ..database import get_session
from ..dependencies import get_cipher
from ..errors import APIError
from ..features import feature_enabled
from ..metrics import LEADERBOARD_LATENCY
from ..models import LeaderboardEntry, Profile
from ..rate_limit import enforce_action_limit
from ..schemas import (
    DailyDefinitionResponse,
    GameConfigSchema,
    GameResponse,
    LeaderboardItem,
    PaginatedLeaderboard,
    StartGameRequest,
)
from ..services import game_response, get_or_create_daily, start_daily

router = APIRouter(prefix="/v1/daily", tags=["daily"])
LEADERBOARD_CACHE_SECONDS = 15


async def require_daily(session: AsyncSession, settings: Settings) -> None:
    if not await feature_enabled(session, settings, "daily"):
        raise APIError(503, "FEATURE_DISABLED", "Daily challenges are temporarily unavailable.")


@router.get("", response_model=DailyDefinitionResponse)
async def get_daily_route(
    _principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    cipher: SecretCipher = Depends(get_cipher),
) -> DailyDefinitionResponse:
    await require_daily(session, settings)
    daily = await get_or_create_daily(session, settings, cipher)
    rollover = datetime.combine(daily.challenge_date + timedelta(days=1), time.min, tzinfo=UTC)
    return DailyDefinitionResponse(
        id=daily.public_id,
        date=daily.challenge_date,
        rule_set_version=daily.rule_set_version,
        derivation_version=daily.derivation_version,
        config=GameConfigSchema.model_validate(daily.config),
        rollover_at=rollover,
    )


@router.post("/start", response_model=GameResponse)
async def start_daily_route(
    request: Request,
    payload: StartGameRequest | None = None,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    cipher: SecretCipher = Depends(get_cipher),
) -> GameResponse:
    await require_daily(session, settings)
    await enforce_action_limit(
        request,
        action="daily.start",
        subject=principal.user_id,
        weight=6,
        integrity_required=True,
    )
    game = await start_daily(
        session, principal, settings, cipher, practice=bool(payload and payload.practice)
    )
    return game_response(game, cipher)


@router.get("/leaderboard", response_model=PaginatedLeaderboard)
async def daily_leaderboard_route(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    cipher: SecretCipher = Depends(get_cipher),
) -> PaginatedLeaderboard:
    started = monotonic_time.perf_counter()
    await require_daily(session, settings)
    daily = await get_or_create_daily(session, settings, cipher)
    category = f"daily:{daily.id}"
    rank_order = (
        LeaderboardEntry.score.desc(),
        LeaderboardEntry.attempts_used,
        LeaderboardEntry.elapsed_seconds,
        LeaderboardEntry.completed_at,
        LeaderboardEntry.id,
    )
    ranking = func.row_number().over(order_by=rank_order).label("rank")
    ranked = (
        select(
            LeaderboardEntry.user_id,
            LeaderboardEntry.score,
            LeaderboardEntry.attempts_used,
            LeaderboardEntry.elapsed_seconds,
            LeaderboardEntry.completed_at,
            LeaderboardEntry.id,
            Profile.display_name,
            ranking,
        )
        .join(Profile, Profile.id == LeaderboardEntry.user_id)
        .where(
            LeaderboardEntry.category == category,
            LeaderboardEntry.review_status == "approved",
            LeaderboardEntry.invalidated_at.is_(None),
            Profile.deleted_at.is_(None),
            Profile.is_banned.is_(False),
            Profile.public_leaderboards.is_(True),
        )
        .subquery()
    )
    redis = request.app.state.redis
    principal_cache_key = hashlib.sha256(str(principal.user_id).encode()).hexdigest()
    cache_version = await leaderboard_cache_version(redis) if redis is not None else 0
    cache_key = (
        f"mastermind:daily-leaderboard:v1:{cache_version}:{daily.id}:"
        f"{page}:{page_size}:{principal_cache_key}"
    )
    if redis is not None and request.app.state.redis_ready:
        try:
            cached = await redis.get(cache_key)
            if cached:
                LEADERBOARD_LATENCY.labels("daily").observe(monotonic_time.perf_counter() - started)
                return PaginatedLeaderboard.model_validate_json(cached)
        except (RedisError, ValueError):
            pass
    rows = (
        await session.execute(
            select(ranked)
            .order_by(ranked.c.rank, ranked.c.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    total = await session.scalar(select(func.count()).select_from(ranked)) or 0
    current_rank = await session.scalar(
        select(func.min(ranked.c.rank)).where(ranked.c.user_id == principal.user_id)
    )
    response = PaginatedLeaderboard(
        items=[
            LeaderboardItem(
                rank=row.rank,
                display_name=row.display_name or "Anonymous breaker",
                score=row.score,
                attempts_used=row.attempts_used,
                elapsed_seconds=row.elapsed_seconds,
                completed_at=row.completed_at,
                is_current_user=row.user_id == principal.user_id,
            )
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
        current_user_rank=current_rank,
    )
    if redis is not None and request.app.state.redis_ready:
        with suppress(RedisError):
            await redis.setex(
                cache_key,
                LEADERBOARD_CACHE_SECONDS,
                response.model_dump_json(by_alias=True),
            )
    LEADERBOARD_LATENCY.labels("daily").observe(monotonic_time.perf_counter() - started)
    return response
