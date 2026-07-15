from __future__ import annotations

from collections import Counter
from datetime import timedelta

from fastapi import APIRouter, Depends, Query, Request, Response, status
from mastermind_core import GameMode, LeaderboardEligibility
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..account import SupabaseAdminClient, get_deletion_provider, process_account_deletion
from ..auth import AuthPrincipal, get_current_user
from ..cache import invalidate_leaderboard_cache
from ..config import Settings, get_settings
from ..crypto import SecretCipher
from ..database import get_session
from ..dependencies import get_cipher
from ..errors import APIError
from ..models import DailyChallenge, GameAttempt, GameSession, UserAchievement
from ..rate_limit import enforce_action_limit
from ..schemas import (
    AchievementProgressSchema,
    DeleteAccountRequest,
    DeleteAccountResponse,
    PaginatedGames,
    ProfileResponse,
    ProfileUpdateRequest,
    StatsResponse,
)
from ..services import (
    ensure_profile,
    export_user_archive,
    game_response,
    normalize_display_name,
    profile_response,
    utcnow,
)

router = APIRouter(prefix="/v1/me", tags=["profile"])
OFFICIAL_STATS_MODES = {GameMode.SOLO.value, GameMode.DAILY.value}


@router.get("/profile", response_model=ProfileResponse)
async def get_profile_route(
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    return await profile_response(session, principal)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile_route(
    payload: ProfileUpdateRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    await enforce_action_limit(
        request,
        action="profile.update",
        subject=principal.user_id,
        weight=10,
    )
    profile = await ensure_profile(session, principal)
    changes = payload.model_fields_set
    if "display_name" in changes:
        if principal.is_anonymous and payload.display_name:
            raise APIError(
                403, "ACCOUNT_UPGRADE_REQUIRED", "Upgrade your guest account to set a name."
            )
        profile.display_name = payload.display_name
        profile.normalized_display_name = (
            normalize_display_name(payload.display_name) if payload.display_name else None
        )
    if "public_leaderboards" in changes and payload.public_leaderboards is not None:
        if principal.is_anonymous and payload.public_leaderboards:
            raise APIError(
                403,
                "ACCOUNT_UPGRADE_REQUIRED",
                "Upgrade your guest account to join public leaderboards.",
            )
        profile.public_leaderboards = payload.public_leaderboards
    await session.commit()
    if changes & {"display_name", "public_leaderboards"}:
        await invalidate_leaderboard_cache(request.app.state.redis)
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        is_anonymous=profile.is_anonymous,
        public_leaderboards=profile.public_leaderboards,
        created_at=profile.created_at,
    )


@router.get("/games", response_model=PaginatedGames)
async def get_games_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
) -> PaginatedGames:
    base = select(GameSession).where(GameSession.owner_id == principal.user_id)
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    games = (
        await session.scalars(
            base.options(selectinload(GameSession.attempts))
            .order_by(GameSession.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return PaginatedGames(
        items=[game_response(game, cipher) for game in games],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats_route(
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StatsResponse:
    await ensure_profile(session, principal)
    games = (
        await session.execute(
            select(
                GameSession.status,
                GameSession.mode,
                GameSession.difficulty,
                GameSession.attempts_used,
                GameSession.final_score,
                GameSession.elapsed_seconds,
                GameSession.ranked_eligibility,
                GameSession.created_at,
                GameSession.daily_challenge_id,
                DailyChallenge.challenge_date,
            )
            .outerjoin(DailyChallenge, DailyChallenge.id == GameSession.daily_challenge_id)
            .where(GameSession.owner_id == principal.user_id)
        )
    ).all()
    played = sum(row.status in {"won", "lost", "abandoned"} for row in games)
    wins = [row for row in games if row.status == "won"]
    losses = sum(row.status == "lost" for row in games)
    abandoned = sum(row.status == "abandoned" for row in games)
    official_wins = [
        row
        for row in wins
        if row.mode in OFFICIAL_STATS_MODES
        and row.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value
    ]
    best: dict[str, int] = {}
    for row in official_wins:
        if row.difficulty and row.final_score is not None:
            best[row.difficulty] = max(best.get(row.difficulty, 0), row.final_score)
    feedback = await session.execute(
        select(
            func.coalesce(func.sum(GameAttempt.black_pegs), 0),
            func.coalesce(func.sum(GameAttempt.white_pegs), 0),
        )
        .join(GameSession, GameSession.id == GameAttempt.game_id)
        .where(GameSession.owner_id == principal.user_id)
    )
    black, white = feedback.one()
    achievements = list(
        await session.scalars(
            select(UserAchievement.achievement_key)
            .where(UserAchievement.user_id == principal.user_id)
            .order_by(UserAchievement.awarded_at)
        )
    )
    mode_counts = Counter(row.mode for row in games)
    fastest = min(
        (row.elapsed_seconds for row in official_wins if row.elapsed_seconds is not None),
        default=None,
    )
    daily_dates = sorted(
        {
            row.challenge_date
            for row in games
            if row.mode == "daily"
            and row.status in {"won", "lost"}
            and row.challenge_date is not None
        },
        reverse=True,
    )
    completed_daily_challenge_ids = {
        row.daily_challenge_id
        for row in games
        if row.mode == GameMode.DAILY.value
        and row.status in {"won", "lost"}
        and row.daily_challenge_id is not None
    }
    streak = 0
    if daily_dates:
        today = utcnow().date()
        latest_eligible = {today, today - timedelta(days=1)}
        if daily_dates[0] in latest_eligible:
            expected = daily_dates[0]
            for day in daily_dates:
                if day != expected:
                    break
                streak += 1
                expected -= timedelta(days=1)
    return StatsResponse(
        games_played=played,
        games_won=len(wins),
        games_lost=losses,
        games_abandoned=abandoned,
        win_rate=round(len(wins) / played * 100, 1) if played else 0.0,
        average_attempts_on_wins=(
            round(sum(row.attempts_used for row in wins) / len(wins), 2) if wins else None
        ),
        best_score_by_difficulty=best,
        daily_streak=streak,
        daily_completion_history=daily_dates[:90],
        fastest_eligible_solve=fastest,
        total_black_pegs=int(black),
        total_white_pegs=int(white),
        favourite_mode=mode_counts.most_common(1)[0][0] if mode_counts else None,
        achievements=achievements,
        achievement_progress={
            "logic_week": AchievementProgressSchema(
                current=min(len(completed_daily_challenge_ids), 7),
                target=7,
            )
        },
    )


@router.get("/export")
async def export_route(
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await enforce_action_limit(
        request,
        action="account.export",
        subject=principal.user_id,
        weight=30,
    )
    if principal.is_anonymous:
        raise APIError(
            403,
            "ACCOUNT_UPGRADE_REQUIRED",
            "Upgrade your guest account before exporting account data.",
        )
    await ensure_profile(session, principal)
    body = await export_user_archive(session, principal)
    return Response(
        body,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="cipherboard-data.zip"'},
    )


@router.delete("", response_model=DeleteAccountResponse, status_code=status.HTTP_200_OK)
async def delete_account_route(
    payload: DeleteAccountRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    provider: SupabaseAdminClient = Depends(get_deletion_provider),
    settings: Settings = Depends(get_settings),
) -> DeleteAccountResponse:
    await enforce_action_limit(
        request,
        action="account.delete",
        subject=principal.user_id,
        weight=30,
    )
    if principal.is_anonymous:
        raise APIError(
            403,
            "ACCOUNT_UPGRADE_REQUIRED",
            "Guest data is removed automatically; upgrade before requesting account deletion.",
        )
    if principal.session_id is None:
        raise APIError(
            401,
            "LIVE_SESSION_REQUIRED",
            "Sign in again before deleting your account.",
        )
    if (
        principal.authenticated_at is None
        or (utcnow() - principal.authenticated_at).total_seconds()
        > settings.admin_recent_auth_seconds
    ):
        raise APIError(
            401,
            "RECENT_AUTH_REQUIRED",
            "Sign in again before deleting your account.",
        )
    authorization = request.headers.get("authorization", "")
    access_token = authorization.removeprefix("Bearer ").strip()
    if not access_token:
        raise APIError(401, "LIVE_SESSION_REQUIRED", "Sign in again before deleting your account.")
    try:
        await process_account_deletion(session, principal, provider, access_token)
    finally:
        # Local privacy changes commit before the identity provider is contacted.
        # Invalidate cached public data even when provider cleanup is interrupted or must retry.
        await invalidate_leaderboard_cache(request.app.state.redis)
    return DeleteAccountResponse(deleted=True)
