from __future__ import annotations

import hashlib
import time
from contextlib import suppress
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, get_current_user
from ..cache import leaderboard_cache_version
from ..config import Settings, get_settings
from ..database import get_session
from ..errors import APIError
from ..features import feature_enabled
from ..metrics import LEADERBOARD_LATENCY
from ..models import LeaderboardEntry, Profile
from ..schemas import LeaderboardItem, PaginatedLeaderboard
from ..services import utcnow

router = APIRouter(prefix="/v1/leaderboards", tags=["leaderboards"])
LEADERBOARD_CACHE_SECONDS = 15


def weekly_period_start(now: datetime) -> datetime:
    """Return Monday 00:00 in the timezone of the supplied server timestamp."""

    return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("", response_model=PaginatedLeaderboard)
async def get_leaderboard_route(
    request: Request,
    period: str = Query(default="all-time", pattern="^(weekly|all-time)$"),
    difficulty: str | None = Query(default=None, pattern="^(easy|normal|hard|expert)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> PaginatedLeaderboard:
    started = time.perf_counter()
    if not await feature_enabled(session, settings, "leaderboards"):
        raise APIError(503, "FEATURE_DISABLED", "Public leaderboards are temporarily unavailable.")
    conditions = [
        LeaderboardEntry.review_status == "approved",
        LeaderboardEntry.invalidated_at.is_(None),
        Profile.deleted_at.is_(None),
        Profile.is_banned.is_(False),
        Profile.public_leaderboards.is_(True),
    ]
    if difficulty:
        conditions.append(LeaderboardEntry.category == difficulty)
    else:
        conditions.append(LeaderboardEntry.category.in_(["easy", "normal", "hard", "expert"]))
    if period == "weekly":
        conditions.append(LeaderboardEntry.completed_at >= weekly_period_start(utcnow()))
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
        .where(*conditions)
        .subquery()
    )
    redis = request.app.state.redis
    principal_cache_key = hashlib.sha256(str(principal.user_id).encode()).hexdigest()
    cache_version = await leaderboard_cache_version(redis) if redis is not None else 0
    cache_key = (
        "mastermind:leaderboard:v1:"
        f"{cache_version}:{period}:{difficulty or 'all'}:{page}:{page_size}:"
        f"{principal_cache_key}"
    )
    if redis is not None and request.app.state.redis_ready:
        try:
            cached = await redis.get(cache_key)
            if cached:
                LEADERBOARD_LATENCY.labels("public").observe(time.perf_counter() - started)
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
    LEADERBOARD_LATENCY.labels("public").observe(time.perf_counter() - started)
    return response
