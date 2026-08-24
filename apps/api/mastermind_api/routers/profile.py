# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `collections` for use in this module.
from collections import Counter

# Imports selected names from `datetime` for use in this module.
from datetime import timedelta

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Query, Request, Response, status

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import GameMode, LeaderboardEligibility

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import func, select

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `sqlalchemy.orm` for use in this module.
from sqlalchemy.orm import selectinload

# Imports selected names from `..account` for use in this module.
from ..account import SupabaseAdminClient, get_deletion_provider, process_account_deletion

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, get_current_user

# Imports selected names from `..cache` for use in this module.
from ..cache import invalidate_leaderboard_cache

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

# Imports selected names from `..models` for use in this module.
from ..models import DailyChallenge, GameAttempt, GameSession, UserAchievement

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import enforce_action_limit

# Imports selected names from `..schemas` for use in this module.
from ..schemas import (
    # Supplies this item to the surrounding call or collection.
    AchievementProgressSchema,
    # Supplies this item to the surrounding call or collection.
    DeleteAccountRequest,
    # Supplies this item to the surrounding call or collection.
    DeleteAccountResponse,
    # Supplies this item to the surrounding call or collection.
    PaginatedGames,
    # Supplies this item to the surrounding call or collection.
    ProfileResponse,
    # Supplies this item to the surrounding call or collection.
    ProfileUpdateRequest,
    # Supplies this item to the surrounding call or collection.
    StatsResponse,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..services` for use in this module.
from ..services import (
    # Supplies this item to the surrounding call or collection.
    ensure_profile,
    # Supplies this item to the surrounding call or collection.
    export_user_archive,
    # Supplies this item to the surrounding call or collection.
    game_response,
    # Supplies this item to the surrounding call or collection.
    normalize_display_name,
    # Supplies this item to the surrounding call or collection.
    profile_response,
    # Supplies this item to the surrounding call or collection.
    utcnow,
    # Closes the multiline call, declaration, or collection started above.
)

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/me", tags=["profile"])
# Computes and stores `OFFICIAL_STATS_MODES` for subsequent operations.
OFFICIAL_STATS_MODES = {GameMode.SOLO.value, GameMode.DAILY.value}


# Applies `@router.get("/profile", response_model=ProfileResponse)` to configure the declaration
# immediately below.
@router.get("/profile", response_model=ProfileResponse)
# Defines the `get_profile_route` callable and its typed interface.
async def get_profile_route(
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> ProfileResponse:
    # Returns this result to the caller and ends the current function.
    return await profile_response(session, principal)


# Applies `@router.patch("/profile", response_model=ProfileResponse)` to configure the declaration
# immediately below.
@router.patch("/profile", response_model=ProfileResponse)
# Defines the `update_profile_route` callable and its typed interface.
async def update_profile_route(
    # Declares the typed `payload` data field.
    payload: ProfileUpdateRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> ProfileResponse:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="profile.update",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `profile` for subsequent operations.
    profile = await ensure_profile(session, principal)
    # Computes and stores `changes` for subsequent operations.
    changes = payload.model_fields_set
    # Checks this condition before executing the nested branch.
    if "display_name" in changes:
        # Checks this condition before executing the nested branch.
        if principal.is_anonymous and payload.display_name:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(
                # Executes this statement as the next step in the surrounding logic.
                403,
                # Supplies this string to the surrounding call or collection.
                "ACCOUNT_UPGRADE_REQUIRED",
                # Supplies this string to the surrounding call or collection.
                "Upgrade your guest account to set a name.",
                # Closes the multiline call, declaration, or collection started above.
            )
        # Computes and stores `profile.display_name` for subsequent operations.
        profile.display_name = payload.display_name
        # Computes and stores `profile.normalized_display_name` for subsequent operations.
        profile.normalized_display_name = (
            # Calls `normalize_display_name` with the supplied values.
            normalize_display_name(payload.display_name) if payload.display_name else None
            # Closes the multiline call, declaration, or collection started above.
        )
    # Checks this condition before executing the nested branch.
    if "public_leaderboards" in changes and payload.public_leaderboards is not None:
        # Checks this condition before executing the nested branch.
        if principal.is_anonymous and payload.public_leaderboards:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(
                # Supplies this item to the surrounding call or collection.
                403,
                # Supplies this item to the surrounding call or collection.
                "ACCOUNT_UPGRADE_REQUIRED",
                # Supplies this item to the surrounding call or collection.
                "Upgrade your guest account to join public leaderboards.",
                # Closes the multiline call, declaration, or collection started above.
            )
        # Computes and stores `profile.public_leaderboards` for subsequent operations.
        profile.public_leaderboards = payload.public_leaderboards
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Checks this condition before executing the nested branch.
    if changes & {"display_name", "public_leaderboards"}:
        # Waits for this asynchronous operation to complete.
        await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns this result to the caller and ends the current function.
    return ProfileResponse(
        # Provides the `id` parameter or keyword argument.
        id=profile.id,
        # Provides the `display_name` parameter or keyword argument.
        display_name=profile.display_name,
        # Provides the `is_anonymous` parameter or keyword argument.
        is_anonymous=profile.is_anonymous,
        # Provides the `public_leaderboards` parameter or keyword argument.
        public_leaderboards=profile.public_leaderboards,
        # Provides the `created_at` parameter or keyword argument.
        created_at=profile.created_at,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/games", response_model=PaginatedGames)` to configure the declaration
# immediately below.
@router.get("/games", response_model=PaginatedGames)
# Defines the `get_games_route` callable and its typed interface.
async def get_games_route(
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=20, ge=1, le=100),
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> PaginatedGames:
    # Executes this statement as the next step in the surrounding logic.
    base = select(GameSession).where(GameSession.owner_id == principal.user_id)
    # Computes and stores `total` for subsequent operations.
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    # Computes and stores `games` for subsequent operations.
    games = (
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `base.options` with the supplied values.
            base.options(selectinload(GameSession.attempts))
            # Executes this statement as the next step in the surrounding logic.
            .order_by(GameSession.created_at.desc())
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return PaginatedGames(
        # Provides the `items` parameter or keyword argument.
        items=[game_response(game, cipher) for game in games],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/stats", response_model=StatsResponse)` to configure the declaration
# immediately below.
@router.get("/stats", response_model=StatsResponse)
# Defines the `get_stats_route` callable and its typed interface.
async def get_stats_route(
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> StatsResponse:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `games` for subsequent operations.
    games = (
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `select` with the supplied values.
            select(
                # Supplies this item to the surrounding call or collection.
                GameSession.status,
                # Supplies this item to the surrounding call or collection.
                GameSession.mode,
                # Supplies this item to the surrounding call or collection.
                GameSession.difficulty,
                # Supplies this item to the surrounding call or collection.
                GameSession.attempts_used,
                # Supplies this item to the surrounding call or collection.
                GameSession.final_score,
                # Supplies this item to the surrounding call or collection.
                GameSession.elapsed_seconds,
                # Supplies this item to the surrounding call or collection.
                GameSession.ranked_eligibility,
                # Supplies this item to the surrounding call or collection.
                GameSession.created_at,
                # Supplies this item to the surrounding call or collection.
                GameSession.daily_challenge_id,
                # Supplies this item to the surrounding call or collection.
                DailyChallenge.challenge_date,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Executes this statement as the next step in the surrounding logic.
            .outerjoin(DailyChallenge, DailyChallenge.id == GameSession.daily_challenge_id)
            # Executes this statement as the next step in the surrounding logic.
            .where(GameSession.owner_id == principal.user_id)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Computes and stores `played` for subsequent operations.
    played = sum(row.status in {"won", "lost", "abandoned"} for row in games)
    # Executes this statement as the next step in the surrounding logic.
    wins = [row for row in games if row.status == "won"]
    # Executes this statement as the next step in the surrounding logic.
    losses = sum(row.status == "lost" for row in games)
    # Executes this statement as the next step in the surrounding logic.
    abandoned = sum(row.status == "abandoned" for row in games)
    # Computes and stores `official_wins` for subsequent operations.
    official_wins = [
        # Executes this statement as the next step in the surrounding logic.
        row
        # Iterates through the supplied values for the nested operation.
        for row in wins
        # Checks this condition before executing the nested branch.
        if row.mode in OFFICIAL_STATS_MODES
        # Executes this statement as the next step in the surrounding logic.
        and row.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Computes and stores `best` for subsequent operations.
    best: dict[str, int] = {}
    # Iterates through the supplied values for the nested operation.
    for row in official_wins:
        # Checks this condition before executing the nested branch.
        if row.difficulty and row.final_score is not None:
            # Executes this statement as the next step in the surrounding logic.
            best[row.difficulty] = max(best.get(row.difficulty, 0), row.final_score)
    # Computes and stores `feedback` for subsequent operations.
    feedback = await session.execute(
        # Calls `select` with the supplied values.
        select(
            # Calls `func.coalesce` with the supplied values.
            func.coalesce(func.sum(GameAttempt.black_pegs), 0),
            # Calls `func.coalesce` with the supplied values.
            func.coalesce(func.sum(GameAttempt.white_pegs), 0),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .join(GameSession, GameSession.id == GameAttempt.game_id)
        # Executes this statement as the next step in the surrounding logic.
        .where(GameSession.owner_id == principal.user_id)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Executes this statement as the next step in the surrounding logic.
    black, white = feedback.one()
    # Computes and stores `achievements` for subsequent operations.
    achievements = list(
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `select` with the supplied values.
            select(UserAchievement.achievement_key)
            # Executes this statement as the next step in the surrounding logic.
            .where(UserAchievement.user_id == principal.user_id)
            # Executes this statement as the next step in the surrounding logic.
            .order_by(UserAchievement.awarded_at)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `mode_counts` for subsequent operations.
    mode_counts = Counter(row.mode for row in games)
    # Computes and stores `fastest` for subsequent operations.
    fastest = min(
        # Supplies this item to the surrounding call or collection.
        (row.elapsed_seconds for row in official_wins if row.elapsed_seconds is not None),
        # Provides the `default` parameter or keyword argument.
        default=None,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `daily_dates` for subsequent operations.
    daily_dates = sorted(
        # Begins the nested block or multiline expression completed below.
        {
            # Executes this statement as the next step in the surrounding logic.
            row.challenge_date
            # Iterates through the supplied values for the nested operation.
            for row in games
            # Checks this condition before executing the nested branch.
            if row.mode == "daily"
            # Executes this statement as the next step in the surrounding logic.
            and row.status in {"won", "lost"}
            # Executes this statement as the next step in the surrounding logic.
            and row.challenge_date is not None
            # Closes the multiline call, declaration, or collection started above.
        },
        # Provides the `reverse` parameter or keyword argument.
        reverse=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `completed_daily_challenge_ids` for subsequent operations.
    completed_daily_challenge_ids = {
        # Executes this statement as the next step in the surrounding logic.
        row.daily_challenge_id
        # Iterates through the supplied values for the nested operation.
        for row in games
        # Checks this condition before executing the nested branch.
        if row.mode == GameMode.DAILY.value
        # Executes this statement as the next step in the surrounding logic.
        and row.status in {"won", "lost"}
        # Executes this statement as the next step in the surrounding logic.
        and row.daily_challenge_id is not None
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `streak` for subsequent operations.
    streak = 0
    # Checks this condition before executing the nested branch.
    if daily_dates:
        # Computes and stores `today` for subsequent operations.
        today = utcnow().date()
        # Computes and stores `latest_eligible` for subsequent operations.
        latest_eligible = {today, today - timedelta(days=1)}
        # Checks this condition before executing the nested branch.
        if daily_dates[0] in latest_eligible:
            # Computes and stores `expected` for subsequent operations.
            expected = daily_dates[0]
            # Iterates through the supplied values for the nested operation.
            for day in daily_dates:
                # Checks this condition before executing the nested branch.
                if day != expected:
                    # Stops the nearest loop after reaching its terminating case.
                    break
                # Executes this statement as the next step in the surrounding logic.
                streak += 1
                # Executes this statement as the next step in the surrounding logic.
                expected -= timedelta(days=1)
    # Returns this result to the caller and ends the current function.
    return StatsResponse(
        # Provides the `games_played` parameter or keyword argument.
        games_played=played,
        # Provides the `games_won` parameter or keyword argument.
        games_won=len(wins),
        # Provides the `games_lost` parameter or keyword argument.
        games_lost=losses,
        # Provides the `games_abandoned` parameter or keyword argument.
        games_abandoned=abandoned,
        # Provides the `win_rate` parameter or keyword argument.
        win_rate=round(len(wins) / played * 100, 1) if played else 0.0,
        # Computes and stores `average_attempts_on_wins` for subsequent operations.
        average_attempts_on_wins=(
            # Calls `round` with the supplied values.
            round(sum(row.attempts_used for row in wins) / len(wins), 2) if wins else None
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Provides the `best_score_by_difficulty` parameter or keyword argument.
        best_score_by_difficulty=best,
        # Provides the `daily_streak` parameter or keyword argument.
        daily_streak=streak,
        # Provides the `daily_completion_history` parameter or keyword argument.
        daily_completion_history=daily_dates[:90],
        # Provides the `fastest_eligible_solve` parameter or keyword argument.
        fastest_eligible_solve=fastest,
        # Provides the `total_black_pegs` parameter or keyword argument.
        total_black_pegs=int(black),
        # Provides the `total_white_pegs` parameter or keyword argument.
        total_white_pegs=int(white),
        # Provides the `favourite_mode` parameter or keyword argument.
        favourite_mode=mode_counts.most_common(1)[0][0] if mode_counts else None,
        # Provides the `achievements` parameter or keyword argument.
        achievements=achievements,
        # Computes and stores `achievement_progress` for subsequent operations.
        achievement_progress={
            # Associates the `logic_week` key with its value.
            "logic_week": AchievementProgressSchema(
                # Provides the `current` parameter or keyword argument.
                current=min(len(completed_daily_challenge_ids), 7),
                # Provides the `target` parameter or keyword argument.
                target=7,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/export")` to configure the declaration immediately below.
@router.get("/export")
# Defines the `export_route` callable and its typed interface.
async def export_route(
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> Response:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="account.export",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=30,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if principal.is_anonymous:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            403,
            # Supplies this item to the surrounding call or collection.
            "ACCOUNT_UPGRADE_REQUIRED",
            # Supplies this item to the surrounding call or collection.
            "Upgrade your guest account before exporting account data.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `body` for subsequent operations.
    body = await export_user_archive(session, principal)
    # Returns this result to the caller and ends the current function.
    return Response(
        # Supplies this item to the surrounding call or collection.
        body,
        # Provides the `media_type` parameter or keyword argument.
        media_type="application/zip",
        # Provides the `headers` parameter or keyword argument.
        headers={"Content-Disposition": 'attachment; filename="cipherboard-data.zip"'},
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.delete("", response_model=DeleteAccountResponse, status_code=status.HTTP_200_OK)`
# to configure the declaration immediately below.
@router.delete("", response_model=DeleteAccountResponse, status_code=status.HTTP_200_OK)
# Defines the `delete_account_route` callable and its typed interface.
async def delete_account_route(
    # Declares the typed `payload` data field.
    payload: DeleteAccountRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `provider` parameter or keyword argument.
    provider: SupabaseAdminClient = Depends(get_deletion_provider),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> DeleteAccountResponse:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="account.delete",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=30,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if principal.is_anonymous:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            403,
            # Supplies this item to the surrounding call or collection.
            "ACCOUNT_UPGRADE_REQUIRED",
            # Supplies this item to the surrounding call or collection.
            "Guest data is removed automatically; upgrade before requesting account deletion.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Checks this condition before executing the nested branch.
    if principal.session_id is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            401,
            # Supplies this item to the surrounding call or collection.
            "LIVE_SESSION_REQUIRED",
            # Supplies this item to the surrounding call or collection.
            "Sign in again before deleting your account.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        principal.authenticated_at is None
        # Executes this statement as the next step in the surrounding logic.
        or (utcnow() - principal.authenticated_at).total_seconds()
        # Executes this statement as the next step in the surrounding logic.
        > settings.admin_recent_auth_seconds
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            401,
            # Supplies this item to the surrounding call or collection.
            "RECENT_AUTH_REQUIRED",
            # Supplies this item to the surrounding call or collection.
            "Sign in again before deleting your account.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `authorization` for subsequent operations.
    authorization = request.headers.get("authorization", "")
    # Computes and stores `access_token` for subsequent operations.
    access_token = authorization.removeprefix("Bearer ").strip()
    # Checks this condition before executing the nested branch.
    if not access_token:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(401, "LIVE_SESSION_REQUIRED", "Sign in again before deleting your account.")
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await process_account_deletion(session, principal, provider, access_token)
    # Runs this cleanup block regardless of the protected result.
    finally:
        # Local privacy changes commit before the identity provider is contacted.
        # Invalidate cached public data even when provider cleanup is interrupted or must retry.
        # Waits for this asynchronous operation to complete.
        await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns this result to the caller and ends the current function.
    return DeleteAccountResponse(deleted=True)
