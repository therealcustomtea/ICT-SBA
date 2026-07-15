from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, require_admin
from ..cache import invalidate_leaderboard_cache
from ..database import get_session
from ..errors import APIError
from ..models import (
    AuditEvent,
    FeatureFlag,
    FriendChallenge,
    GameSession,
    LeaderboardEntry,
    ModerationAction,
    MultiplayerMember,
    MultiplayerRoom,
    Profile,
)
from ..rate_limit import enforce_action_limit
from ..schemas import (
    AdminActionRequest,
    AdminChallengeItem,
    AdminGameItem,
    AdminLeaderboardItem,
    AdminPage,
    AdminProfileItem,
    AdminRoomItem,
    AdminSummary,
    AuditEventResponse,
    FeatureFlagResponse,
    ProfileUpdateRequest,
)
from ..services import normalize_display_name, utcnow

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def audit(
    session: AsyncSession,
    principal: AuthPrincipal,
    action: str,
    target_type: str,
    target_id: object,
    reason: str | None,
) -> None:
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            reason=reason,
            event_data={},
        )
    )


@router.get("/games", response_model=AdminPage[AdminGameItem])
async def games_route(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminPage[AdminGameItem]:
    query = select(GameSession)
    if status_filter:
        query = query.where(GameSession.status == status_filter)
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    games = (
        await session.scalars(
            query.order_by(GameSession.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return AdminPage[AdminGameItem](
        items=[
            AdminGameItem(
                id=game.public_id,
                owner_id=game.owner_id,
                mode=game.mode,
                status=game.status,
                difficulty=game.difficulty,
                attempts_used=game.attempts_used,
                max_attempts=game.maximum_attempts,
                score=game.final_score,
                ranked_eligibility=game.ranked_eligibility,
                started_at=game.started_at,
                completed_at=game.completed_at,
            )
            for game in games
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/profiles", response_model=AdminPage[AdminProfileItem])
async def profiles_route(
    moderation_only: bool = Query(default=False),
    search: str | None = Query(default=None, min_length=2, max_length=32),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminPage[AdminProfileItem]:
    query = select(Profile)
    if moderation_only:
        query = query.where(Profile.is_banned.is_(True))
    if search:
        query = query.where(
            Profile.normalized_display_name.contains(normalize_display_name(search))
        )
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    profiles = (
        await session.scalars(
            query.order_by(Profile.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return AdminPage[AdminProfileItem](
        items=[
            AdminProfileItem(
                id=profile.id,
                display_name=profile.display_name,
                is_anonymous=profile.is_anonymous,
                public_leaderboards=profile.public_leaderboards,
                is_banned=profile.is_banned,
                deleted_at=profile.deleted_at,
                created_at=profile.created_at,
            )
            for profile in profiles
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/rooms", response_model=AdminPage[AdminRoomItem])
async def rooms_route(
    active_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminPage[AdminRoomItem]:
    member_counts = (
        select(MultiplayerMember.room_id, func.count(MultiplayerMember.id).label("member_count"))
        .group_by(MultiplayerMember.room_id)
        .subquery()
    )
    query = select(MultiplayerRoom, func.coalesce(member_counts.c.member_count, 0)).outerjoin(
        member_counts, member_counts.c.room_id == MultiplayerRoom.id
    )
    if active_only:
        query = query.where(MultiplayerRoom.status.in_(["waiting", "active"]))
    total = (
        await session.scalar(
            select(func.count()).select_from(query.with_only_columns(MultiplayerRoom.id).subquery())
        )
        or 0
    )
    rows = (
        await session.execute(
            query.order_by(MultiplayerRoom.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return AdminPage[AdminRoomItem](
        items=[
            AdminRoomItem(
                id=room.id,
                status=room.status,
                member_count=member_count,
                winner_id=room.winner_id,
                is_tie=room.is_tie,
                expires_at=room.expires_at,
                created_at=room.created_at,
            )
            for room, member_count in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/challenges", response_model=AdminPage[AdminChallengeItem])
async def challenges_route(
    active_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminPage[AdminChallengeItem]:
    completed_count = (
        select(func.count(GameSession.id))
        .where(
            GameSession.friend_challenge_id == FriendChallenge.id,
            GameSession.completed_at.is_not(None),
        )
        .correlate(FriendChallenge)
        .scalar_subquery()
    )
    query = select(FriendChallenge, completed_count.label("completed_count"))
    if active_only:
        query = query.where(
            FriendChallenge.revoked_at.is_(None), FriendChallenge.expires_at > utcnow()
        )
    total = (
        await session.scalar(
            select(func.count()).select_from(query.with_only_columns(FriendChallenge.id).subquery())
        )
        or 0
    )
    rows = (
        await session.execute(
            query.order_by(FriendChallenge.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return AdminPage[AdminChallengeItem](
        items=[
            AdminChallengeItem(
                id=challenge.id,
                creator_id=challenge.creator_id,
                title=challenge.title,
                completed_count=completed,
                revoked_at=challenge.revoked_at,
                expires_at=challenge.expires_at,
                created_at=challenge.created_at,
            )
            for challenge, completed in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/leaderboard-review", response_model=AdminPage[AdminLeaderboardItem])
async def leaderboard_review_route(
    review_status: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminPage[AdminLeaderboardItem]:
    query = select(LeaderboardEntry)
    if review_status:
        query = query.where(LeaderboardEntry.review_status == review_status)
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    entries = (
        await session.scalars(
            query.order_by(LeaderboardEntry.completed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return AdminPage[AdminLeaderboardItem](
        items=[
            AdminLeaderboardItem(
                id=entry.id,
                game_id=entry.game_id,
                user_id=entry.user_id,
                category=entry.category,
                score=entry.score,
                attempts_used=entry.attempts_used,
                elapsed_seconds=entry.elapsed_seconds,
                review_status=entry.review_status,
                invalidated_at=entry.invalidated_at,
                completed_at=entry.completed_at,
            )
            for entry in entries
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/summary", response_model=AdminSummary)
async def summary_route(
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminSummary:
    return AdminSummary(
        profiles=await session.scalar(select(func.count(Profile.id))) or 0,
        active_games=await session.scalar(
            select(func.count(GameSession.id)).where(GameSession.status == "active")
        )
        or 0,
        completed_games=await session.scalar(
            select(func.count(GameSession.id)).where(GameSession.completed_at.is_not(None))
        )
        or 0,
        active_rooms=await session.scalar(
            select(func.count(MultiplayerRoom.id)).where(
                MultiplayerRoom.status.in_(["waiting", "active"])
            )
        )
        or 0,
        pending_review_entries=await session.scalar(
            select(func.count(LeaderboardEntry.id)).where(
                LeaderboardEntry.review_status == "pending"
            )
        )
        or 0,
    )


@router.get("/flags", response_model=list[FeatureFlagResponse])
async def flags_route(
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[FeatureFlagResponse]:
    flags = (await session.scalars(select(FeatureFlag).order_by(FeatureFlag.key))).all()
    return [FeatureFlagResponse(key=flag.key, enabled=flag.enabled) for flag in flags]


@router.patch("/flags/{key}", response_model=FeatureFlagResponse)
async def update_flag_route(
    key: str,
    payload: AdminActionRequest,
    request: Request,
    principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> FeatureFlagResponse:
    await enforce_action_limit(
        request,
        action="admin.flag.update",
        subject=principal.user_id,
        resource=key,
        weight=10,
        integrity_required=True,
    )
    if payload.enabled is None:
        raise APIError(422, "ENABLED_REQUIRED", "Provide the desired enabled state.")
    flag = await session.get(FeatureFlag, key)
    if flag is None:
        raise APIError(404, "FEATURE_FLAG_NOT_FOUND", "Feature flag not found.")
    flag.enabled = payload.enabled
    audit(session, principal, "feature_flag.updated", "feature_flag", key, payload.reason)
    await session.commit()
    return FeatureFlagResponse(key=flag.key, enabled=flag.enabled)


@router.post("/leaderboard/{entry_id}/invalidate")
async def invalidate_leaderboard_route(
    entry_id: uuid.UUID,
    payload: AdminActionRequest,
    request: Request,
    principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await enforce_action_limit(
        request,
        action="admin.leaderboard.invalidate",
        subject=principal.user_id,
        resource=entry_id,
        weight=10,
        integrity_required=True,
    )
    entry = await session.get(LeaderboardEntry, entry_id)
    if entry is None:
        raise APIError(404, "LEADERBOARD_ENTRY_NOT_FOUND", "Leaderboard entry not found.")
    entry.invalidated_at = utcnow()
    entry.review_status = "invalidated"
    audit(
        session, principal, "leaderboard.invalidated", "leaderboard_entry", entry_id, payload.reason
    )
    await session.commit()
    await invalidate_leaderboard_cache(request.app.state.redis)
    return {"invalidated": True}


@router.post("/leaderboard/{entry_id}/restore")
async def restore_leaderboard_route(
    entry_id: uuid.UUID,
    payload: AdminActionRequest,
    request: Request,
    principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await enforce_action_limit(
        request,
        action="admin.leaderboard.restore",
        subject=principal.user_id,
        resource=entry_id,
        weight=10,
        integrity_required=True,
    )
    entry = await session.get(LeaderboardEntry, entry_id)
    if entry is None:
        raise APIError(404, "LEADERBOARD_ENTRY_NOT_FOUND", "Leaderboard entry not found.")
    entry.invalidated_at = None
    entry.review_status = "approved"
    audit(session, principal, "leaderboard.restored", "leaderboard_entry", entry_id, payload.reason)
    await session.commit()
    await invalidate_leaderboard_cache(request.app.state.redis)
    return {"restored": True}


@router.post("/profiles/{user_id}/moderate")
async def moderate_profile_route(
    user_id: uuid.UUID,
    payload: AdminActionRequest,
    request: Request,
    principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await enforce_action_limit(
        request,
        action="admin.profile.moderate",
        subject=principal.user_id,
        resource=user_id,
        weight=10,
        integrity_required=True,
    )
    if user_id == principal.user_id:
        raise APIError(
            409,
            "ADMIN_SELF_MODERATION_FORBIDDEN",
            "Use another authorized administrator for this account.",
        )
    profile = await session.get(Profile, user_id)
    if profile is None:
        raise APIError(404, "PROFILE_NOT_FOUND", "Profile not found.")
    if payload.enabled is not None:
        profile.is_banned = payload.enabled
    if payload.display_name is not None:
        safe_name = ProfileUpdateRequest(display_name=payload.display_name).display_name
        profile.display_name = safe_name
        profile.normalized_display_name = normalize_display_name(safe_name or "") or None
    session.add(
        ModerationAction(
            actor_id=principal.user_id,
            target_user_id=user_id,
            action="ban" if profile.is_banned else "unban_or_rename",
            reason=payload.reason,
        )
    )
    audit(session, principal, "profile.moderated", "profile", user_id, payload.reason)
    await session.commit()
    await invalidate_leaderboard_cache(request.app.state.redis)
    return {"updated": True}


@router.post("/challenges/{challenge_id}/revoke")
async def admin_revoke_challenge_route(
    challenge_id: uuid.UUID,
    payload: AdminActionRequest,
    request: Request,
    principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await enforce_action_limit(
        request,
        action="admin.challenge.revoke",
        subject=principal.user_id,
        resource=challenge_id,
        weight=10,
        integrity_required=True,
    )
    challenge = await session.get(FriendChallenge, challenge_id)
    if challenge is None:
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    challenge.revoked_at = utcnow()
    audit(session, principal, "challenge.revoked", "friend_challenge", challenge_id, payload.reason)
    await session.commit()
    return {"revoked": True}


@router.post("/rooms/{room_id}/terminate")
async def terminate_room_route(
    room_id: uuid.UUID,
    payload: AdminActionRequest,
    request: Request,
    principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await enforce_action_limit(
        request,
        action="admin.room.terminate",
        subject=principal.user_id,
        resource=room_id,
        weight=10,
        integrity_required=True,
    )
    room = await session.get(MultiplayerRoom, room_id)
    if room is None:
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found.")
    room.status = "terminated"
    audit(session, principal, "room.terminated", "multiplayer_room", room_id, payload.reason)
    await session.commit()
    return {"terminated": True}


@router.get("/audit", response_model=list[AuditEventResponse])
async def audit_route(
    limit: int = Query(default=100, ge=1, le=250),
    _principal: AuthPrincipal = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AuditEventResponse]:
    events = (
        await session.scalars(
            select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
        )
    ).all()
    return [
        AuditEventResponse(
            id=event.id,
            actor_id=event.actor_id,
            action=event.action,
            target_type=event.target_type,
            target_id=event.target_id,
            reason=event.reason,
            created_at=event.created_at,
        )
        for event in events
    ]
