# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports `time as monotonic_time` so the module can use that dependency.
import time as monotonic_time

# Imports selected names from `contextlib` for use in this module.
from contextlib import suppress

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, time, timedelta

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Query, Request

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import func, select

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, get_current_user

# Imports selected names from `..cache` for use in this module.
from ..cache import leaderboard_cache_version

# Imports selected names from `..config` for use in this module.
from ..config import Settings, get_settings

# Imports selected names from `..crypto` for use in this module.
from ..crypto import SecretCipher

# Imports selected names from `..database` for use in this module.
from ..database import get_session

# Imports selected names from `..dependencies` for use in this module.
from ..dependencies import get_cipher

# Imports selected names from `..errors` for use in this module.
from ..errors import APIError

# Imports selected names from `..features` for use in this module.
from ..features import feature_enabled

# Imports selected names from `..metrics` for use in this module.
from ..metrics import LEADERBOARD_LATENCY

# Imports selected names from `..models` for use in this module.
from ..models import LeaderboardEntry, Profile

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import enforce_action_limit

# Imports selected names from `..schemas` for use in this module.
from ..schemas import (
    # Supplies this item to the surrounding call or collection.
    DailyDefinitionResponse,
    # Supplies this item to the surrounding call or collection.
    GameConfigSchema,
    # Supplies this item to the surrounding call or collection.
    GameResponse,
    # Supplies this item to the surrounding call or collection.
    LeaderboardItem,
    # Supplies this item to the surrounding call or collection.
    PaginatedLeaderboard,
    # Supplies this item to the surrounding call or collection.
    StartGameRequest,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..services` for use in this module.
from ..services import game_response, get_or_create_daily, start_daily

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/daily", tags=["daily"])
# Computes and stores `LEADERBOARD_CACHE_SECONDS` for subsequent operations.
LEADERBOARD_CACHE_SECONDS = 15


# Defines the `require_daily` callable and its typed interface.
async def require_daily(session: AsyncSession, settings: Settings) -> None:
    # Checks this condition before executing the nested branch.
    if not await feature_enabled(session, settings, "daily"):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "FEATURE_DISABLED", "Daily challenges are temporarily unavailable.")


# Applies `@router.get("", response_model=DailyDefinitionResponse)` to configure the declaration
# immediately below.
@router.get("", response_model=DailyDefinitionResponse)
# Defines the `get_daily_route` callable and its typed interface.
async def get_daily_route(
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> DailyDefinitionResponse:
    # Waits for this asynchronous operation to complete.
    await require_daily(session, settings)
    # Computes and stores `daily` for subsequent operations.
    daily = await get_or_create_daily(session, settings, cipher)
    # Computes and stores `rollover` for subsequent operations.
    rollover = datetime.combine(daily.challenge_date + timedelta(days=1), time.min, tzinfo=UTC)
    # Returns this result to the caller and ends the current function.
    return DailyDefinitionResponse(
        # Provides the `id` parameter or keyword argument.
        id=daily.public_id,
        # Provides the `date` parameter or keyword argument.
        date=daily.challenge_date,
        # Provides the `rule_set_version` parameter or keyword argument.
        rule_set_version=daily.rule_set_version,
        # Provides the `derivation_version` parameter or keyword argument.
        derivation_version=daily.derivation_version,
        # Provides the `config` parameter or keyword argument.
        config=GameConfigSchema.model_validate(daily.config),
        # Provides the `rollover_at` parameter or keyword argument.
        rollover_at=rollover,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.post("/start", response_model=GameResponse)` to configure the declaration
# immediately below.
@router.post("/start", response_model=GameResponse)
# Defines the `start_daily_route` callable and its typed interface.
async def start_daily_route(
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `payload` parameter or keyword argument.
    payload: StartGameRequest | None = None,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> GameResponse:
    # Waits for this asynchronous operation to complete.
    await require_daily(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="daily.start",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=6,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game` for subsequent operations.
    game = await start_daily(
        # Executes this statement as the next step in the surrounding logic.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        settings,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `practice` value to the surrounding call.
        practice=bool(payload and payload.practice),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return game_response(game, cipher)


# Applies `@router.get("/leaderboard", response_model=PaginatedLeaderboard)` to configure the
# declaration immediately below.
@router.get("/leaderboard", response_model=PaginatedLeaderboard)
# Defines the `daily_leaderboard_route` callable and its typed interface.
async def daily_leaderboard_route(
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=25, ge=1, le=100),
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> PaginatedLeaderboard:
    # Computes and stores `started` for subsequent operations.
    started = monotonic_time.perf_counter()
    # Waits for this asynchronous operation to complete.
    await require_daily(session, settings)
    # Computes and stores `daily` for subsequent operations.
    daily = await get_or_create_daily(session, settings, cipher)
    # Computes and stores `category` for subsequent operations.
    category = f"daily:{daily.id}"
    # Computes and stores `rank_order` for subsequent operations.
    rank_order = (
        # Calls `LeaderboardEntry.score.desc` with the supplied values.
        LeaderboardEntry.score.desc(),
        # Supplies this item to the surrounding call or collection.
        LeaderboardEntry.attempts_used,
        # Supplies this item to the surrounding call or collection.
        LeaderboardEntry.elapsed_seconds,
        # Supplies this item to the surrounding call or collection.
        LeaderboardEntry.completed_at,
        # Supplies this item to the surrounding call or collection.
        LeaderboardEntry.id,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `ranking` for subsequent operations.
    ranking = func.row_number().over(order_by=rank_order).label("rank")
    # Computes and stores `ranked` for subsequent operations.
    ranked = (
        # Calls `select` with the supplied values.
        select(
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.user_id,
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.score,
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.attempts_used,
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.elapsed_seconds,
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.completed_at,
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.id,
            # Supplies this item to the surrounding call or collection.
            Profile.display_name,
            # Supplies this item to the surrounding call or collection.
            ranking,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .join(Profile, Profile.id == LeaderboardEntry.user_id)
        # Begins the nested block or multiline expression completed below.
        .where(
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.category == category,
            # Supplies this item to the surrounding call or collection.
            LeaderboardEntry.review_status == "approved",
            # Calls `LeaderboardEntry.invalidated_at.is_` with the supplied values.
            LeaderboardEntry.invalidated_at.is_(None),
            # Calls `Profile.deleted_at.is_` with the supplied values.
            Profile.deleted_at.is_(None),
            # Calls `Profile.is_banned.is_` with the supplied values.
            Profile.is_banned.is_(False),
            # Calls `Profile.public_leaderboards.is_` with the supplied values.
            Profile.public_leaderboards.is_(True),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .subquery()
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `redis` for subsequent operations.
    redis = request.app.state.redis
    # Computes and stores `principal_cache_key` for subsequent operations.
    principal_cache_key = hashlib.sha256(str(principal.user_id).encode()).hexdigest()
    # Computes and stores `cache_version` for subsequent operations.
    cache_version = await leaderboard_cache_version(redis) if redis is not None else 0
    # Computes and stores `cache_key` for subsequent operations.
    cache_key = (
        # Executes this statement as the next step in the surrounding logic.
        f"mastermind:daily-leaderboard:v1:{cache_version}:{daily.id}:"
        # Executes this statement as the next step in the surrounding logic.
        f"{page}:{page_size}:{principal_cache_key}"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if redis is not None and request.app.state.redis_ready:
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `cached` for subsequent operations.
            cached = await redis.get(cache_key)
            # Checks this condition before executing the nested branch.
            if cached:
                # Calls `LEADERBOARD_LATENCY.labels` with the supplied values.
                LEADERBOARD_LATENCY.labels("daily").observe(monotonic_time.perf_counter() - started)
                # Returns this result to the caller and ends the current function.
                return PaginatedLeaderboard.model_validate_json(cached)
        # Handles the listed exception so failure remains controlled.
        except (RedisError, ValueError):
            # Provides the intentionally empty statement required by Python syntax.
            pass
    # Computes and stores `rows` for subsequent operations.
    rows = (
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `select` with the supplied values.
            select(ranked)
            # Executes this statement as the next step in the surrounding logic.
            .order_by(ranked.c.rank, ranked.c.id)
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Computes and stores `total` for subsequent operations.
    total = await session.scalar(select(func.count()).select_from(ranked)) or 0
    # Computes and stores `current_rank` for subsequent operations.
    current_rank = await session.scalar(
        # Calls `select` with the supplied values.
        select(func.min(ranked.c.rank)).where(ranked.c.user_id == principal.user_id)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `response` for subsequent operations.
    response = PaginatedLeaderboard(
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `LeaderboardItem` with the supplied values.
            LeaderboardItem(
                # Provides the `rank` parameter or keyword argument.
                rank=row.rank,
                # Provides the `display_name` parameter or keyword argument.
                display_name=row.display_name or "Anonymous breaker",
                # Provides the `score` parameter or keyword argument.
                score=row.score,
                # Provides the `attempts_used` parameter or keyword argument.
                attempts_used=row.attempts_used,
                # Provides the `elapsed_seconds` parameter or keyword argument.
                elapsed_seconds=row.elapsed_seconds,
                # Provides the `completed_at` parameter or keyword argument.
                completed_at=row.completed_at,
                # Provides the `is_current_user` parameter or keyword argument.
                is_current_user=row.user_id == principal.user_id,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for row in rows
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Provides the `current_user_rank` parameter or keyword argument.
        current_user_rank=current_rank,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if redis is not None and request.app.state.redis_ready:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError):
            # Waits for this asynchronous operation to complete.
            await redis.setex(
                # Supplies this item to the surrounding call or collection.
                cache_key,
                # Supplies this item to the surrounding call or collection.
                LEADERBOARD_CACHE_SECONDS,
                # Uses the current HTTP request or response in this operation.
                response.model_dump_json(by_alias=True),
                # Closes the multiline call, declaration, or collection started above.
            )
    # Calls `LEADERBOARD_LATENCY.labels` with the supplied values.
    LEADERBOARD_LATENCY.labels("daily").observe(monotonic_time.perf_counter() - started)
    # Returns this result to the caller and ends the current function.
    return response
