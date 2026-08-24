# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Query, Request

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import func, select

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, require_admin

# Imports selected names from `..cache` for use in this module.
from ..cache import invalidate_leaderboard_cache

# Imports selected names from `..database` for use in this module.
from ..database import get_session

# Imports selected names from `..errors` for use in this module.
from ..errors import APIError

# Imports selected names from `..models` for use in this module.
from ..models import (
    # Supplies this item to the surrounding call or collection.
    AuditEvent,
    # Supplies this item to the surrounding call or collection.
    FeatureFlag,
    # Supplies this item to the surrounding call or collection.
    FriendChallenge,
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    LeaderboardEntry,
    # Supplies this item to the surrounding call or collection.
    ModerationAction,
    # Supplies this item to the surrounding call or collection.
    MultiplayerMember,
    # Supplies this item to the surrounding call or collection.
    MultiplayerRoom,
    # Supplies this item to the surrounding call or collection.
    Profile,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import enforce_action_limit

# Imports selected names from `..schemas` for use in this module.
from ..schemas import (
    # Supplies this item to the surrounding call or collection.
    AdminActionRequest,
    # Supplies this item to the surrounding call or collection.
    AdminChallengeItem,
    # Supplies this item to the surrounding call or collection.
    AdminGameItem,
    # Supplies this item to the surrounding call or collection.
    AdminLeaderboardItem,
    # Supplies this item to the surrounding call or collection.
    AdminPage,
    # Supplies this item to the surrounding call or collection.
    AdminProfileItem,
    # Supplies this item to the surrounding call or collection.
    AdminRoomItem,
    # Supplies this item to the surrounding call or collection.
    AdminSummary,
    # Supplies this item to the surrounding call or collection.
    AuditEventResponse,
    # Supplies this item to the surrounding call or collection.
    FeatureFlagResponse,
    # Supplies this item to the surrounding call or collection.
    ProfileUpdateRequest,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..services` for use in this module.
from ..services import normalize_display_name, utcnow

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/admin", tags=["admin"])


# Defines the `audit` callable and its typed interface.
def audit(
    # Declares the typed `session` data field.
    session: AsyncSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `action` data field.
    action: str,
    # Declares the typed `target_type` data field.
    target_type: str,
    # Declares the typed `target_id` data field.
    target_id: object,
    # Declares the typed `reason` data field.
    reason: str | None,
    # Completes the signature and declares the callable return type.
) -> None:
    # Calls `session.add` with the supplied values.
    session.add(
        # Calls `AuditEvent` with the supplied values.
        AuditEvent(
            # Provides the `actor_id` parameter or keyword argument.
            actor_id=principal.user_id,
            # Provides the `action` parameter or keyword argument.
            action=action,
            # Provides the `target_type` parameter or keyword argument.
            target_type=target_type,
            # Provides the `target_id` parameter or keyword argument.
            target_id=str(target_id),
            # Provides the `reason` parameter or keyword argument.
            reason=reason,
            # Provides the `event_data` parameter or keyword argument.
            event_data={},
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/games", response_model=AdminPage[AdminGameItem])` to configure the
# declaration immediately below.
@router.get("/games", response_model=AdminPage[AdminGameItem])
# Defines the `games_route` callable and its typed interface.
async def games_route(
    # Provides the `status_filter` parameter or keyword argument.
    status_filter: str | None = Query(default=None, alias="status"),
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=50, ge=1, le=100),
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AdminPage[AdminGameItem]:
    # Computes and stores `query` for subsequent operations.
    query = select(GameSession)
    # Checks this condition before executing the nested branch.
    if status_filter:
        # Executes this statement as the next step in the surrounding logic.
        query = query.where(GameSession.status == status_filter)
    # Computes and stores `total` for subsequent operations.
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    # Computes and stores `games` for subsequent operations.
    games = (
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `query.order_by` with the supplied values.
            query.order_by(GameSession.created_at.desc())
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return AdminPage[AdminGameItem](
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `AdminGameItem` with the supplied values.
            AdminGameItem(
                # Provides the `id` parameter or keyword argument.
                id=game.public_id,
                # Provides the `owner_id` parameter or keyword argument.
                owner_id=game.owner_id,
                # Provides the `mode` parameter or keyword argument.
                mode=game.mode,
                # Provides the `status` parameter or keyword argument.
                status=game.status,
                # Provides the `difficulty` parameter or keyword argument.
                difficulty=game.difficulty,
                # Provides the `attempts_used` parameter or keyword argument.
                attempts_used=game.attempts_used,
                # Provides the `max_attempts` parameter or keyword argument.
                max_attempts=game.maximum_attempts,
                # Provides the `score` parameter or keyword argument.
                score=game.final_score,
                # Provides the `ranked_eligibility` parameter or keyword argument.
                ranked_eligibility=game.ranked_eligibility,
                # Provides the `started_at` parameter or keyword argument.
                started_at=game.started_at,
                # Provides the `completed_at` parameter or keyword argument.
                completed_at=game.completed_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for game in games
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/profiles", response_model=AdminPage[AdminProfileItem])` to configure the
# declaration immediately below.
@router.get("/profiles", response_model=AdminPage[AdminProfileItem])
# Defines the `profiles_route` callable and its typed interface.
async def profiles_route(
    # Provides the `moderation_only` parameter or keyword argument.
    moderation_only: bool = Query(default=False),
    # Provides the `search` parameter or keyword argument.
    search: str | None = Query(default=None, min_length=2, max_length=32),
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=50, ge=1, le=100),
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AdminPage[AdminProfileItem]:
    # Computes and stores `query` for subsequent operations.
    query = select(Profile)
    # Checks this condition before executing the nested branch.
    if moderation_only:
        # Computes and stores `query` for subsequent operations.
        query = query.where(Profile.is_banned.is_(True))
    # Checks this condition before executing the nested branch.
    if search:
        # Computes and stores `query` for subsequent operations.
        query = query.where(
            # Calls `Profile.normalized_display_name.contains` with the supplied values.
            Profile.normalized_display_name.contains(normalize_display_name(search))
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `total` for subsequent operations.
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    # Computes and stores `profiles` for subsequent operations.
    profiles = (
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `query.order_by` with the supplied values.
            query.order_by(Profile.created_at.desc())
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return AdminPage[AdminProfileItem](
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `AdminProfileItem` with the supplied values.
            AdminProfileItem(
                # Provides the `id` parameter or keyword argument.
                id=profile.id,
                # Provides the `display_name` parameter or keyword argument.
                display_name=profile.display_name,
                # Provides the `is_anonymous` parameter or keyword argument.
                is_anonymous=profile.is_anonymous,
                # Provides the `public_leaderboards` parameter or keyword argument.
                public_leaderboards=profile.public_leaderboards,
                # Provides the `is_banned` parameter or keyword argument.
                is_banned=profile.is_banned,
                # Provides the `deleted_at` parameter or keyword argument.
                deleted_at=profile.deleted_at,
                # Provides the `created_at` parameter or keyword argument.
                created_at=profile.created_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for profile in profiles
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/rooms", response_model=AdminPage[AdminRoomItem])` to configure the
# declaration immediately below.
@router.get("/rooms", response_model=AdminPage[AdminRoomItem])
# Defines the `rooms_route` callable and its typed interface.
async def rooms_route(
    # Provides the `active_only` parameter or keyword argument.
    active_only: bool = Query(default=False),
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=50, ge=1, le=100),
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AdminPage[AdminRoomItem]:
    # Computes and stores `member_counts` for subsequent operations.
    member_counts = (
        # Calls `select` with the supplied values.
        select(MultiplayerMember.room_id, func.count(MultiplayerMember.id).label("member_count"))
        # Executes this statement as the next step in the surrounding logic.
        .group_by(MultiplayerMember.room_id)
        # Executes this statement as the next step in the surrounding logic.
        .subquery()
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `query` for subsequent operations.
    query = select(MultiplayerRoom, func.coalesce(member_counts.c.member_count, 0)).outerjoin(
        # Executes this statement as the next step in the surrounding logic.
        member_counts,
        # Supplies this item to the surrounding call or collection.
        member_counts.c.room_id == MultiplayerRoom.id,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if active_only:
        # Computes and stores `query` for subsequent operations.
        query = query.where(MultiplayerRoom.status.in_(["waiting", "active"]))
    # Computes and stores `total` for subsequent operations.
    total = (
        # Waits for this asynchronous operation to complete.
        await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count()).select_from(query.with_only_columns(MultiplayerRoom.id).subquery())
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        or 0
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `rows` for subsequent operations.
    rows = (
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `query.order_by` with the supplied values.
            query.order_by(MultiplayerRoom.created_at.desc())
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return AdminPage[AdminRoomItem](
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `AdminRoomItem` with the supplied values.
            AdminRoomItem(
                # Provides the `id` parameter or keyword argument.
                id=room.id,
                # Provides the `status` parameter or keyword argument.
                status=room.status,
                # Provides the `member_count` parameter or keyword argument.
                member_count=member_count,
                # Provides the `winner_id` parameter or keyword argument.
                winner_id=room.winner_id,
                # Provides the `is_tie` parameter or keyword argument.
                is_tie=room.is_tie,
                # Provides the `expires_at` parameter or keyword argument.
                expires_at=room.expires_at,
                # Provides the `created_at` parameter or keyword argument.
                created_at=room.created_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for room, member_count in rows
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/challenges", response_model=AdminPage[AdminChallengeItem])` to configure
# the declaration immediately below.
@router.get("/challenges", response_model=AdminPage[AdminChallengeItem])
# Defines the `challenges_route` callable and its typed interface.
async def challenges_route(
    # Provides the `active_only` parameter or keyword argument.
    active_only: bool = Query(default=False),
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=50, ge=1, le=100),
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AdminPage[AdminChallengeItem]:
    # Computes and stores `completed_count` for subsequent operations.
    completed_count = (
        # Calls `select` with the supplied values.
        select(func.count(GameSession.id))
        # Begins the nested block or multiline expression completed below.
        .where(
            # Supplies this item to the surrounding call or collection.
            GameSession.friend_challenge_id == FriendChallenge.id,
            # Calls `GameSession.completed_at.is_not` with the supplied values.
            GameSession.completed_at.is_not(None),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        .correlate(FriendChallenge)
        # Executes this statement as the next step in the surrounding logic.
        .scalar_subquery()
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `query` for subsequent operations.
    query = select(FriendChallenge, completed_count.label("completed_count"))
    # Checks this condition before executing the nested branch.
    if active_only:
        # Computes and stores `query` for subsequent operations.
        query = query.where(
            # Calls `FriendChallenge.revoked_at.is_` with the supplied values.
            FriendChallenge.revoked_at.is_(None),
            # Supplies this item to the surrounding call or collection.
            FriendChallenge.expires_at > utcnow(),
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `total` for subsequent operations.
    total = (
        # Waits for this asynchronous operation to complete.
        await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count()).select_from(query.with_only_columns(FriendChallenge.id).subquery())
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        or 0
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `rows` for subsequent operations.
    rows = (
        # Waits for this asynchronous operation to complete.
        await session.execute(
            # Calls `query.order_by` with the supplied values.
            query.order_by(FriendChallenge.created_at.desc())
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return AdminPage[AdminChallengeItem](
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `AdminChallengeItem` with the supplied values.
            AdminChallengeItem(
                # Provides the `id` parameter or keyword argument.
                id=challenge.id,
                # Provides the `creator_id` parameter or keyword argument.
                creator_id=challenge.creator_id,
                # Provides the `title` parameter or keyword argument.
                title=challenge.title,
                # Provides the `completed_count` parameter or keyword argument.
                completed_count=completed,
                # Provides the `revoked_at` parameter or keyword argument.
                revoked_at=challenge.revoked_at,
                # Provides the `expires_at` parameter or keyword argument.
                expires_at=challenge.expires_at,
                # Provides the `created_at` parameter or keyword argument.
                created_at=challenge.created_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for challenge, completed in rows
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/leaderboard-review", response_model=AdminPage[AdminLeaderboardItem])` to
# configure the declaration immediately below.
@router.get("/leaderboard-review", response_model=AdminPage[AdminLeaderboardItem])
# Defines the `leaderboard_review_route` callable and its typed interface.
async def leaderboard_review_route(
    # Provides the `review_status` parameter or keyword argument.
    review_status: str | None = Query(default=None, alias="status"),
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=50, ge=1, le=100),
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AdminPage[AdminLeaderboardItem]:
    # Computes and stores `query` for subsequent operations.
    query = select(LeaderboardEntry)
    # Checks this condition before executing the nested branch.
    if review_status:
        # Executes this statement as the next step in the surrounding logic.
        query = query.where(LeaderboardEntry.review_status == review_status)
    # Computes and stores `total` for subsequent operations.
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    # Computes and stores `entries` for subsequent operations.
    entries = (
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `query.order_by` with the supplied values.
            query.order_by(LeaderboardEntry.completed_at.desc())
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return AdminPage[AdminLeaderboardItem](
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `AdminLeaderboardItem` with the supplied values.
            AdminLeaderboardItem(
                # Provides the `id` parameter or keyword argument.
                id=entry.id,
                # Provides the `game_id` parameter or keyword argument.
                game_id=entry.game_id,
                # Provides the `user_id` parameter or keyword argument.
                user_id=entry.user_id,
                # Provides the `category` parameter or keyword argument.
                category=entry.category,
                # Provides the `score` parameter or keyword argument.
                score=entry.score,
                # Provides the `attempts_used` parameter or keyword argument.
                attempts_used=entry.attempts_used,
                # Provides the `elapsed_seconds` parameter or keyword argument.
                elapsed_seconds=entry.elapsed_seconds,
                # Provides the `review_status` parameter or keyword argument.
                review_status=entry.review_status,
                # Provides the `invalidated_at` parameter or keyword argument.
                invalidated_at=entry.invalidated_at,
                # Provides the `completed_at` parameter or keyword argument.
                completed_at=entry.completed_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for entry in entries
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Provides the `page` parameter or keyword argument.
        page=page,
        # Provides the `page_size` parameter or keyword argument.
        page_size=page_size,
        # Provides the `total` parameter or keyword argument.
        total=total,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/summary", response_model=AdminSummary)` to configure the declaration
# immediately below.
@router.get("/summary", response_model=AdminSummary)
# Defines the `summary_route` callable and its typed interface.
async def summary_route(
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> AdminSummary:
    # Returns this result to the caller and ends the current function.
    return AdminSummary(
        # Provides the `profiles` parameter or keyword argument.
        profiles=await session.scalar(select(func.count(Profile.id))) or 0,
        # Computes and stores `active_games` for subsequent operations.
        active_games=await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(GameSession.id)).where(GameSession.status == "active")
            # Closes the multiline call, declaration, or collection started above.
        )
        # Supplies this item to the surrounding call or collection.
        or 0,
        # Computes and stores `completed_games` for subsequent operations.
        completed_games=await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(GameSession.id)).where(GameSession.completed_at.is_not(None))
            # Closes the multiline call, declaration, or collection started above.
        )
        # Supplies this item to the surrounding call or collection.
        or 0,
        # Computes and stores `active_rooms` for subsequent operations.
        active_rooms=await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(MultiplayerRoom.id)).where(
                # Calls `MultiplayerRoom.status.in_` with the supplied values.
                MultiplayerRoom.status.in_(["waiting", "active"])
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Supplies this item to the surrounding call or collection.
        or 0,
        # Computes and stores `pending_review_entries` for subsequent operations.
        pending_review_entries=await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count(LeaderboardEntry.id)).where(
                # Executes this statement as the next step in the surrounding logic.
                LeaderboardEntry.review_status == "pending"
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Supplies this item to the surrounding call or collection.
        or 0,
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@router.get("/flags", response_model=list[FeatureFlagResponse])` to configure the
# declaration immediately below.
@router.get("/flags", response_model=list[FeatureFlagResponse])
# Defines the `flags_route` callable and its typed interface.
async def flags_route(
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> list[FeatureFlagResponse]:
    # Computes and stores `flags` for subsequent operations.
    flags = (await session.scalars(select(FeatureFlag).order_by(FeatureFlag.key))).all()
    # Returns this result to the caller and ends the current function.
    return [FeatureFlagResponse(key=flag.key, enabled=flag.enabled) for flag in flags]


# Applies `@router.patch("/flags/{key}", response_model=FeatureFlagResponse)` to configure the
# declaration immediately below.
@router.patch("/flags/{key}", response_model=FeatureFlagResponse)
# Defines the `update_flag_route` callable and its typed interface.
async def update_flag_route(
    # Declares the typed `key` data field.
    key: str,
    # Declares the typed `payload` data field.
    payload: AdminActionRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> FeatureFlagResponse:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="admin.flag.update",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=key,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if payload.enabled is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(422, "ENABLED_REQUIRED", "Provide the desired enabled state.")
    # Computes and stores `flag` for subsequent operations.
    flag = await session.get(FeatureFlag, key)
    # Checks this condition before executing the nested branch.
    if flag is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "FEATURE_FLAG_NOT_FOUND", "Feature flag not found.")
    # Computes and stores `flag.enabled` for subsequent operations.
    flag.enabled = payload.enabled
    # Calls `audit` with the supplied values.
    audit(session, principal, "feature_flag.updated", "feature_flag", key, payload.reason)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return FeatureFlagResponse(key=flag.key, enabled=flag.enabled)


# Applies `@router.post("/leaderboard/{entry_id}/invalidate")` to configure the declaration
# immediately below.
@router.post("/leaderboard/{entry_id}/invalidate")
# Defines the `invalidate_leaderboard_route` callable and its typed interface.
async def invalidate_leaderboard_route(
    # Declares the typed `entry_id` data field.
    entry_id: uuid.UUID,
    # Declares the typed `payload` data field.
    payload: AdminActionRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> dict[str, bool]:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="admin.leaderboard.invalidate",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=entry_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `entry` for subsequent operations.
    entry = await session.get(LeaderboardEntry, entry_id)
    # Checks this condition before executing the nested branch.
    if entry is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "LEADERBOARD_ENTRY_NOT_FOUND", "Leaderboard entry not found.")
    # Computes and stores `entry.invalidated_at` for subsequent operations.
    entry.invalidated_at = utcnow()
    # Computes and stores `entry.review_status` for subsequent operations.
    entry.review_status = "invalidated"
    # Calls `audit` with the supplied values.
    audit(
        # Executes this statement as the next step in the surrounding logic.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this string to the surrounding call or collection.
        "leaderboard.invalidated",
        # Supplies this string to the surrounding call or collection.
        "leaderboard_entry",
        # Supplies this item to the surrounding call or collection.
        entry_id,
        # Supplies this item to the surrounding call or collection.
        payload.reason,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Waits for this asynchronous operation to complete.
    await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns this result to the caller and ends the current function.
    return {"invalidated": True}


# Applies `@router.post("/leaderboard/{entry_id}/restore")` to configure the declaration immediately
# below.
@router.post("/leaderboard/{entry_id}/restore")
# Defines the `restore_leaderboard_route` callable and its typed interface.
async def restore_leaderboard_route(
    # Declares the typed `entry_id` data field.
    entry_id: uuid.UUID,
    # Declares the typed `payload` data field.
    payload: AdminActionRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> dict[str, bool]:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="admin.leaderboard.restore",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=entry_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `entry` for subsequent operations.
    entry = await session.get(LeaderboardEntry, entry_id)
    # Checks this condition before executing the nested branch.
    if entry is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "LEADERBOARD_ENTRY_NOT_FOUND", "Leaderboard entry not found.")
    # Computes and stores `entry.invalidated_at` for subsequent operations.
    entry.invalidated_at = None
    # Computes and stores `entry.review_status` for subsequent operations.
    entry.review_status = "approved"
    # Calls `audit` with the supplied values.
    audit(session, principal, "leaderboard.restored", "leaderboard_entry", entry_id, payload.reason)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Waits for this asynchronous operation to complete.
    await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns this result to the caller and ends the current function.
    return {"restored": True}


# Applies `@router.post("/profiles/{user_id}/moderate")` to configure the declaration immediately
# below.
@router.post("/profiles/{user_id}/moderate")
# Defines the `moderate_profile_route` callable and its typed interface.
async def moderate_profile_route(
    # Declares the typed `user_id` data field.
    user_id: uuid.UUID,
    # Declares the typed `payload` data field.
    payload: AdminActionRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> dict[str, bool]:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="admin.profile.moderate",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if user_id == principal.user_id:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            409,
            # Supplies this item to the surrounding call or collection.
            "ADMIN_SELF_MODERATION_FORBIDDEN",
            # Supplies this item to the surrounding call or collection.
            "Use another authorized administrator for this account.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, user_id)
    # Checks this condition before executing the nested branch.
    if profile is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "PROFILE_NOT_FOUND", "Profile not found.")
    # Checks this condition before executing the nested branch.
    if payload.enabled is not None:
        # Computes and stores `profile.is_banned` for subsequent operations.
        profile.is_banned = payload.enabled
    # Checks this condition before executing the nested branch.
    if payload.display_name is not None:
        # Computes and stores `safe_name` for subsequent operations.
        safe_name = ProfileUpdateRequest(display_name=payload.display_name).display_name
        # Computes and stores `profile.display_name` for subsequent operations.
        profile.display_name = safe_name
        # Computes and stores `profile.normalized_display_name` for subsequent operations.
        profile.normalized_display_name = normalize_display_name(safe_name or "") or None
    # Calls `session.add` with the supplied values.
    session.add(
        # Calls `ModerationAction` with the supplied values.
        ModerationAction(
            # Provides the `actor_id` parameter or keyword argument.
            actor_id=principal.user_id,
            # Provides the `target_user_id` parameter or keyword argument.
            target_user_id=user_id,
            # Provides the `action` parameter or keyword argument.
            action="ban" if profile.is_banned else "unban_or_rename",
            # Provides the `reason` parameter or keyword argument.
            reason=payload.reason,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `audit` with the supplied values.
    audit(session, principal, "profile.moderated", "profile", user_id, payload.reason)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Waits for this asynchronous operation to complete.
    await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns this result to the caller and ends the current function.
    return {"updated": True}


# Applies `@router.post("/challenges/{challenge_id}/revoke")` to configure the declaration
# immediately below.
@router.post("/challenges/{challenge_id}/revoke")
# Defines the `admin_revoke_challenge_route` callable and its typed interface.
async def admin_revoke_challenge_route(
    # Declares the typed `challenge_id` data field.
    challenge_id: uuid.UUID,
    # Declares the typed `payload` data field.
    payload: AdminActionRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> dict[str, bool]:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="admin.challenge.revoke",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=challenge_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `challenge` for subsequent operations.
    challenge = await session.get(FriendChallenge, challenge_id)
    # Checks this condition before executing the nested branch.
    if challenge is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    # Computes and stores `challenge.revoked_at` for subsequent operations.
    challenge.revoked_at = utcnow()
    # Calls `audit` with the supplied values.
    audit(session, principal, "challenge.revoked", "friend_challenge", challenge_id, payload.reason)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return {"revoked": True}


# Applies `@router.post("/rooms/{room_id}/terminate")` to configure the declaration immediately
# below.
@router.post("/rooms/{room_id}/terminate")
# Defines the `terminate_room_route` callable and its typed interface.
async def terminate_room_route(
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `payload` data field.
    payload: AdminActionRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> dict[str, bool]:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="admin.room.terminate",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=room_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `room` for subsequent operations.
    room = await session.get(MultiplayerRoom, room_id)
    # Checks this condition before executing the nested branch.
    if room is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found.")
    # Computes and stores `room.status` for subsequent operations.
    room.status = "terminated"
    # Calls `audit` with the supplied values.
    audit(session, principal, "room.terminated", "multiplayer_room", room_id, payload.reason)
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return {"terminated": True}


# Applies `@router.get("/audit", response_model=list[AuditEventResponse])` to configure the
# declaration immediately below.
@router.get("/audit", response_model=list[AuditEventResponse])
# Defines the `audit_route` callable and its typed interface.
async def audit_route(
    # Provides the `limit` parameter or keyword argument.
    limit: int = Query(default=100, ge=1, le=250),
    # Provides the `_principal` parameter or keyword argument.
    _principal: AuthPrincipal = Depends(require_admin),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Completes the signature and declares the callable return type.
) -> list[AuditEventResponse]:
    # Computes and stores `events` for subsequent operations.
    events = (
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `select` with the supplied values.
            select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return [
        # Calls `AuditEventResponse` with the supplied values.
        AuditEventResponse(
            # Provides the `id` parameter or keyword argument.
            id=event.id,
            # Provides the `actor_id` parameter or keyword argument.
            actor_id=event.actor_id,
            # Provides the `action` parameter or keyword argument.
            action=event.action,
            # Provides the `target_type` parameter or keyword argument.
            target_type=event.target_type,
            # Provides the `target_id` parameter or keyword argument.
            target_id=event.target_id,
            # Provides the `reason` parameter or keyword argument.
            reason=event.reason,
            # Provides the `created_at` parameter or keyword argument.
            created_at=event.created_at,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Iterates through the supplied values for the nested operation.
        for event in events
        # Closes the multiline call, declaration, or collection started above.
    ]
