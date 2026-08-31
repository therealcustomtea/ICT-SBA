# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `re` because this module uses that dependency.
import re

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `fastapi` for this module.
from fastapi import APIRouter, Depends, Query, Request

# Imports the required names from `..auth` for this module.
from ..auth import AuthPrincipal, require_admin

# Imports the required names from `..cache` for this module.
from ..cache import invalidate_leaderboard_cache

# Imports the required names from `..database` for this module.
from ..database import DESCENDING, MongoSession, get_session

# Imports the required names from `..errors` for this module.
from ..errors import APIError

# Imports the required names from `..models` for this module.
from ..models import (
    # Supplies this required nested value.
    AuditEvent,
    # Supplies this required nested value.
    FeatureFlag,
    # Supplies this required nested value.
    FriendChallenge,
    # Supplies this required nested value.
    GameSession,
    # Supplies this required nested value.
    LeaderboardEntry,
    # Supplies this required nested value.
    ModerationAction,
    # Supplies this required nested value.
    MultiplayerMember,
    # Supplies this required nested value.
    MultiplayerRoom,
    # Supplies this required nested value.
    Profile,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports the required names from `..rate_limit` for this module.
from ..rate_limit import enforce_action_limit

# Imports the required names from `..schemas` for this module.
from ..schemas import (
    # Supplies this required nested value.
    AdminActionRequest,
    # Supplies this required nested value.
    AdminChallengeItem,
    # Supplies this required nested value.
    AdminGameItem,
    # Supplies this required nested value.
    AdminLeaderboardItem,
    # Supplies this required nested value.
    AdminPage,
    # Supplies this required nested value.
    AdminProfileItem,
    # Supplies this required nested value.
    AdminRoomItem,
    # Supplies this required nested value.
    AdminSummary,
    # Supplies this required nested value.
    AuditEventResponse,
    # Supplies this required nested value.
    FeatureFlagResponse,
    # Supplies this required nested value.
    ProfileUpdateRequest,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports the required names from `..services` for this module.
from ..services import normalize_display_name, utcnow

# Stores `router` because later steps depend on this value.
router = APIRouter(prefix="/v1/admin", tags=["admin"])


# Defines this callable to implement the operation described by its name.
def audit(
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Declares this typed field so the surrounding contract is explicit.
    principal: AuthPrincipal,
    # Declares this typed field so the surrounding contract is explicit.
    action: str,
    # Declares this typed field so the surrounding contract is explicit.
    target_type: str,
    # Declares this typed field so the surrounding contract is explicit.
    target_id: object,
    # Declares this typed field so the surrounding contract is explicit.
    reason: str | None,
    # Closes the multiline declaration, call, or collection opened above.
) -> None:
    # Supplies this required nested value.
    session.add(
        # Supplies this required nested value.
        AuditEvent(
            # Stores `actor_id` because later steps depend on this value.
            actor_id=principal.user_id,
            # Stores `action` because later steps depend on this value.
            action=action,
            # Stores `target_type` because later steps depend on this value.
            target_type=target_type,
            # Stores `target_id` because later steps depend on this value.
            target_id=str(target_id),
            # Stores `reason` because later steps depend on this value.
            reason=reason,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.get("/games", response_model=AdminPage[AdminGameItem])
# Defines this callable to implement the operation described by its name.
async def games_route(
    # Stores `status_filter` because later steps depend on this value.
    status_filter: str | None = Query(default=None, alias="status"),
    # Stores `page` because later steps depend on this value.
    page: int = Query(default=1, ge=1),
    # Stores `page_size` because later steps depend on this value.
    page_size: int = Query(default=50, ge=1, le=100),
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AdminPage[AdminGameItem]:
    # Stores `match` because later steps depend on this value.
    match = {"status": status_filter} if status_filter else {}
    # Stores `total` because later steps depend on this value.
    total = await session.count(GameSession, match)
    # Stores `games` because later steps depend on this value.
    games = await session.find_many(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        match,
        # Stores `sort` because later steps depend on this value.
        sort=[("created_at", DESCENDING)],
        # Stores `skip` because later steps depend on this value.
        skip=(page - 1) * page_size,
        # Stores `limit` because later steps depend on this value.
        limit=page_size,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Returns the computed result and ends the current callable.
    return AdminPage[AdminGameItem](
        # Stores `items` because later steps depend on this value.
        items=[
            # Supplies this required nested value.
            AdminGameItem(
                # Stores `id` because later steps depend on this value.
                id=game.public_id,
                # Stores `owner_id` because later steps depend on this value.
                owner_id=game.owner_id,
                # Stores `mode` because later steps depend on this value.
                mode=game.mode,
                # Stores `status` because later steps depend on this value.
                status=game.status,
                # Stores `difficulty` because later steps depend on this value.
                difficulty=game.difficulty,
                # Stores `attempts_used` because later steps depend on this value.
                attempts_used=game.attempts_used,
                # Stores `max_attempts` because later steps depend on this value.
                max_attempts=game.maximum_attempts,
                # Stores `score` because later steps depend on this value.
                score=game.final_score,
                # Stores `ranked_eligibility` because later steps depend on this value.
                ranked_eligibility=game.ranked_eligibility,
                # Stores `started_at` because later steps depend on this value.
                started_at=game.started_at,
                # Stores `completed_at` because later steps depend on this value.
                completed_at=game.completed_at,
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Iterates over these values so each item receives the same processing.
            for game in games
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Stores `page` because later steps depend on this value.
        page=page,
        # Stores `page_size` because later steps depend on this value.
        page_size=page_size,
        # Stores `total` because later steps depend on this value.
        total=total,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.get("/profiles", response_model=AdminPage[AdminProfileItem])
# Defines this callable to implement the operation described by its name.
async def profiles_route(
    # Stores `moderation_only` because later steps depend on this value.
    moderation_only: bool = Query(default=False),
    # Stores `search` because later steps depend on this value.
    search: str | None = Query(default=None, min_length=2, max_length=32),
    # Stores `page` because later steps depend on this value.
    page: int = Query(default=1, ge=1),
    # Stores `page_size` because later steps depend on this value.
    page_size: int = Query(default=50, ge=1, le=100),
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AdminPage[AdminProfileItem]:
    # Stores `match` because later steps depend on this value.
    match: dict[str, object] = {}
    # Guards the nested operation so it runs only when this condition is satisfied.
    if moderation_only:
        # Supplies this required nested value.
        match["is_banned"] = True
    # Guards the nested operation so it runs only when this condition is satisfied.
    if search:
        # Supplies this required nested value.
        match["normalized_display_name"] = {
            # Supplies this literal value to the surrounding declaration or call.
            "$regex": re.escape(normalize_display_name(search)),
            # Supplies this literal value to the surrounding declaration or call.
            "$options": "i",
            # Closes the multiline declaration, call, or collection opened above.
        }
    # Stores `total` because later steps depend on this value.
    total = await session.count(Profile, match)
    # Stores `profiles` because later steps depend on this value.
    profiles = await session.find_many(
        # Supplies this required nested value.
        Profile,
        # Supplies this required nested value.
        match,
        # Stores `sort` because later steps depend on this value.
        sort=[("created_at", DESCENDING)],
        # Stores `skip` because later steps depend on this value.
        skip=(page - 1) * page_size,
        # Stores `limit` because later steps depend on this value.
        limit=page_size,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Returns the computed result and ends the current callable.
    return AdminPage[AdminProfileItem](
        # Stores `items` because later steps depend on this value.
        items=[
            # Supplies this required nested value.
            AdminProfileItem(
                # Stores `id` because later steps depend on this value.
                id=profile.id,
                # Stores `display_name` because later steps depend on this value.
                display_name=profile.display_name,
                # Stores `is_anonymous` because later steps depend on this value.
                is_anonymous=profile.is_anonymous,
                # Stores `public_leaderboards` because later steps depend on this value.
                public_leaderboards=profile.public_leaderboards,
                # Stores `is_banned` because later steps depend on this value.
                is_banned=profile.is_banned,
                # Stores `deleted_at` because later steps depend on this value.
                deleted_at=profile.deleted_at,
                # Stores `created_at` because later steps depend on this value.
                created_at=profile.created_at,
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Iterates over these values so each item receives the same processing.
            for profile in profiles
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Stores `page` because later steps depend on this value.
        page=page,
        # Stores `page_size` because later steps depend on this value.
        page_size=page_size,
        # Stores `total` because later steps depend on this value.
        total=total,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.get("/rooms", response_model=AdminPage[AdminRoomItem])
# Defines this callable to implement the operation described by its name.
async def rooms_route(
    # Stores `active_only` because later steps depend on this value.
    active_only: bool = Query(default=False),
    # Stores `page` because later steps depend on this value.
    page: int = Query(default=1, ge=1),
    # Stores `page_size` because later steps depend on this value.
    page_size: int = Query(default=50, ge=1, le=100),
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AdminPage[AdminRoomItem]:
    # Stores `match` because later steps depend on this value.
    match = {"status": {"$in": ["waiting", "active"]}} if active_only else {}
    # Stores `total` because later steps depend on this value.
    total = await session.count(MultiplayerRoom, match)
    # Stores `rooms` because later steps depend on this value.
    rooms = await session.find_many(
        # Supplies this required nested value.
        MultiplayerRoom,
        # Supplies this required nested value.
        match,
        # Stores `sort` because later steps depend on this value.
        sort=[("created_at", DESCENDING)],
        # Stores `skip` because later steps depend on this value.
        skip=(page - 1) * page_size,
        # Stores `limit` because later steps depend on this value.
        limit=page_size,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `items` because later steps depend on this value.
    items = []
    # Iterates over these values so each item receives the same processing.
    for room in rooms:
        # Supplies this required nested value.
        items.append(
            # Supplies this required nested value.
            AdminRoomItem(
                # Stores `id` because later steps depend on this value.
                id=room.id,
                # Stores `status` because later steps depend on this value.
                status=room.status,
                # Stores `member_count` because later steps depend on this value.
                member_count=await session.count(MultiplayerMember, {"room_id": room.id}),
                # Stores `winner_id` because later steps depend on this value.
                winner_id=room.winner_id,
                # Stores `is_tie` because later steps depend on this value.
                is_tie=room.is_tie,
                # Stores `expires_at` because later steps depend on this value.
                expires_at=room.expires_at,
                # Stores `created_at` because later steps depend on this value.
                created_at=room.created_at,
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Returns the computed result and ends the current callable.
    return AdminPage[AdminRoomItem](items=items, page=page, page_size=page_size, total=total)


# Applies this decorator to configure the declaration immediately below.
@router.get("/challenges", response_model=AdminPage[AdminChallengeItem])
# Defines this callable to implement the operation described by its name.
async def challenges_route(
    # Stores `active_only` because later steps depend on this value.
    active_only: bool = Query(default=False),
    # Stores `page` because later steps depend on this value.
    page: int = Query(default=1, ge=1),
    # Stores `page_size` because later steps depend on this value.
    page_size: int = Query(default=50, ge=1, le=100),
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AdminPage[AdminChallengeItem]:
    # Stores `match` because later steps depend on this value.
    match: dict[str, object] = {}
    # Guards the nested operation so it runs only when this condition is satisfied.
    if active_only:
        # Stores `match` because later steps depend on this value.
        match = {"revoked_at": None, "expires_at": {"$gt": utcnow()}}
    # Stores `total` because later steps depend on this value.
    total = await session.count(FriendChallenge, match)
    # Stores `challenges` because later steps depend on this value.
    challenges = await session.find_many(
        # Supplies this required nested value.
        FriendChallenge,
        # Supplies this required nested value.
        match,
        # Stores `sort` because later steps depend on this value.
        sort=[("created_at", DESCENDING)],
        # Stores `skip` because later steps depend on this value.
        skip=(page - 1) * page_size,
        # Stores `limit` because later steps depend on this value.
        limit=page_size,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `items` because later steps depend on this value.
    items = []
    # Iterates over these values so each item receives the same processing.
    for challenge in challenges:
        # Supplies this required nested value.
        items.append(
            # Supplies this required nested value.
            AdminChallengeItem(
                # Stores `id` because later steps depend on this value.
                id=challenge.id,
                # Stores `creator_id` because later steps depend on this value.
                creator_id=challenge.creator_id,
                # Stores `title` because later steps depend on this value.
                title=challenge.title,
                # Stores `completed_count` because later steps depend on this value.
                completed_count=await session.count(
                    # Supplies this required nested value.
                    GameSession,
                    # Supplies this required nested value.
                    {"friend_challenge_id": challenge.id, "completed_at": {"$ne": None}},
                    # Closes the multiline declaration, call, or collection opened above.
                ),
                # Stores `revoked_at` because later steps depend on this value.
                revoked_at=challenge.revoked_at,
                # Stores `expires_at` because later steps depend on this value.
                expires_at=challenge.expires_at,
                # Stores `created_at` because later steps depend on this value.
                created_at=challenge.created_at,
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Returns the computed result and ends the current callable.
    return AdminPage[AdminChallengeItem](
        # Stores `items` because later steps depend on this value.
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.get("/leaderboard-review", response_model=AdminPage[AdminLeaderboardItem])
# Defines this callable to implement the operation described by its name.
async def leaderboard_review_route(
    # Stores `review_status` because later steps depend on this value.
    review_status: str | None = Query(default=None, alias="status"),
    # Stores `page` because later steps depend on this value.
    page: int = Query(default=1, ge=1),
    # Stores `page_size` because later steps depend on this value.
    page_size: int = Query(default=50, ge=1, le=100),
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AdminPage[AdminLeaderboardItem]:
    # Stores `match` because later steps depend on this value.
    match = {"review_status": review_status} if review_status else {}
    # Stores `total` because later steps depend on this value.
    total = await session.count(LeaderboardEntry, match)
    # Stores `entries` because later steps depend on this value.
    entries = await session.find_many(
        # Supplies this required nested value.
        LeaderboardEntry,
        # Supplies this required nested value.
        match,
        # Stores `sort` because later steps depend on this value.
        sort=[("completed_at", DESCENDING)],
        # Stores `skip` because later steps depend on this value.
        skip=(page - 1) * page_size,
        # Stores `limit` because later steps depend on this value.
        limit=page_size,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Returns the computed result and ends the current callable.
    return AdminPage[AdminLeaderboardItem](
        # Stores `items` because later steps depend on this value.
        items=[
            # Supplies this required nested value.
            AdminLeaderboardItem(
                # Stores `id` because later steps depend on this value.
                id=entry.id,
                # Stores `game_id` because later steps depend on this value.
                game_id=entry.game_id,
                # Stores `user_id` because later steps depend on this value.
                user_id=entry.user_id,
                # Stores `category` because later steps depend on this value.
                category=entry.category,
                # Stores `score` because later steps depend on this value.
                score=entry.score,
                # Stores `attempts_used` because later steps depend on this value.
                attempts_used=entry.attempts_used,
                # Stores `elapsed_seconds` because later steps depend on this value.
                elapsed_seconds=entry.elapsed_seconds,
                # Stores `review_status` because later steps depend on this value.
                review_status=entry.review_status,
                # Stores `invalidated_at` because later steps depend on this value.
                invalidated_at=entry.invalidated_at,
                # Stores `completed_at` because later steps depend on this value.
                completed_at=entry.completed_at,
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Iterates over these values so each item receives the same processing.
            for entry in entries
            # Closes the multiline declaration, call, or collection opened above.
        ],
        # Stores `page` because later steps depend on this value.
        page=page,
        # Stores `page_size` because later steps depend on this value.
        page_size=page_size,
        # Stores `total` because later steps depend on this value.
        total=total,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.get("/summary", response_model=AdminSummary)
# Defines this callable to implement the operation described by its name.
async def summary_route(
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> AdminSummary:
    # Returns the computed result and ends the current callable.
    return AdminSummary(
        # Stores `profiles` because later steps depend on this value.
        profiles=await session.count(Profile),
        # Stores `active_games` because later steps depend on this value.
        active_games=await session.count(GameSession, {"status": "active"}),
        # Stores `completed_games` because later steps depend on this value.
        completed_games=await session.count(GameSession, {"completed_at": {"$ne": None}}),
        # Stores `active_rooms` because later steps depend on this value.
        active_rooms=await session.count(
            # Supplies this required nested value.
            MultiplayerRoom,
            {"status": {"$in": ["waiting", "active"]}},
            # Closes the multiline declaration, call, or collection opened above.
        ),
        # Stores `pending_review_entries` because later steps depend on this value.
        pending_review_entries=await session.count(
            # Supplies this required nested value.
            LeaderboardEntry,
            {"review_status": "pending"},
            # Closes the multiline declaration, call, or collection opened above.
        ),
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.get("/flags", response_model=list[FeatureFlagResponse])
# Defines this callable to implement the operation described by its name.
async def flags_route(
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> list[FeatureFlagResponse]:
    # Stores `flags` because later steps depend on this value.
    flags = await session.find_many(FeatureFlag, sort=[("_id", 1)])
    # Returns the computed result and ends the current callable.
    return [FeatureFlagResponse(key=flag.key, enabled=flag.enabled) for flag in flags]


# Applies this decorator to configure the declaration immediately below.
@router.patch("/flags/{key}", response_model=FeatureFlagResponse)
# Defines this callable to implement the operation described by its name.
async def update_flag_route(
    # Declares this typed field so the surrounding contract is explicit.
    key: str,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> FeatureFlagResponse:
    # Performs this required operation before the surrounding flow continues.
    await _admin_limit(request, principal, "admin.flag.update", key)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if payload.enabled is None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(422, "ENABLED_REQUIRED", "Provide the desired enabled state.")
    # Stores `flag` because later steps depend on this value.
    flag = await session.get(FeatureFlag, key)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if flag is None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(404, "FEATURE_FLAG_NOT_FOUND", "Feature flag not found.")
    # Stores `flag.enabled` because later steps depend on this value.
    flag.enabled = payload.enabled
    # Supplies this required nested value.
    audit(session, principal, "feature_flag.updated", "feature_flag", key, payload.reason)
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Returns the computed result and ends the current callable.
    return FeatureFlagResponse(key=flag.key, enabled=flag.enabled)


# Defines this callable to implement the operation described by its name.
async def _admin_limit(
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    principal: AuthPrincipal,
    action: str,
    resource: object,
    # Closes the multiline declaration, call, or collection opened above.
) -> None:
    # Performs this required operation before the surrounding flow continues.
    await enforce_action_limit(
        # Supplies this required nested value.
        request,
        # Stores `action` because later steps depend on this value.
        action=action,
        # Stores `subject` because later steps depend on this value.
        subject=principal.user_id,
        # Stores `resource` because later steps depend on this value.
        resource=resource,
        # Stores `weight` because later steps depend on this value.
        weight=10,
        # Stores `integrity_required` because later steps depend on this value.
        integrity_required=True,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Defines this callable to implement the operation described by its name.
async def _set_leaderboard_state(
    # Declares this typed field so the surrounding contract is explicit.
    entry_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Declares this typed field so the surrounding contract is explicit.
    principal: AuthPrincipal,
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Supplies this required nested value.
    *,
    # Declares this typed field so the surrounding contract is explicit.
    invalidated: bool,
    # Closes the multiline declaration, call, or collection opened above.
) -> dict[str, bool]:
    # Stores `action` because later steps depend on this value.
    action = "invalidate" if invalidated else "restore"
    # Performs this required operation before the surrounding flow continues.
    await _admin_limit(request, principal, f"admin.leaderboard.{action}", entry_id)
    # Stores `entry` because later steps depend on this value.
    entry = await session.get(LeaderboardEntry, entry_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if entry is None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(404, "LEADERBOARD_ENTRY_NOT_FOUND", "Leaderboard entry not found.")
    # Stores `entry.invalidated_at` because later steps depend on this value.
    entry.invalidated_at = utcnow() if invalidated else None
    # Stores `entry.review_status` because later steps depend on this value.
    entry.review_status = "invalidated" if invalidated else "approved"
    # Supplies this required nested value.
    audit(
        # Supplies this required nested value.
        session,
        # Supplies this required nested value.
        principal,
        # Supplies this required nested value.
        f"leaderboard.{action}d",
        # Supplies this literal value to the surrounding declaration or call.
        "leaderboard_entry",
        # Supplies this required nested value.
        entry_id,
        # Supplies this required nested value.
        payload.reason,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Performs this required operation before the surrounding flow continues.
    await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns the computed result and ends the current callable.
    return {f"{action}d": True}


# Applies this decorator to configure the declaration immediately below.
@router.post("/leaderboard/{entry_id}/invalidate")
# Defines this callable to implement the operation described by its name.
async def invalidate_leaderboard_route(
    # Declares this typed field so the surrounding contract is explicit.
    entry_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> dict[str, bool]:
    # Returns the computed result and ends the current callable.
    return await _set_leaderboard_state(
        # Supplies this required nested value.
        entry_id,
        payload,
        request,
        principal,
        session,
        invalidated=True,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.post("/leaderboard/{entry_id}/restore")
# Defines this callable to implement the operation described by its name.
async def restore_leaderboard_route(
    # Declares this typed field so the surrounding contract is explicit.
    entry_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> dict[str, bool]:
    # Returns the computed result and ends the current callable.
    return await _set_leaderboard_state(
        # Supplies this required nested value.
        entry_id,
        payload,
        request,
        principal,
        session,
        invalidated=False,
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@router.post("/profiles/{user_id}/moderate")
# Defines this callable to implement the operation described by its name.
async def moderate_profile_route(
    # Declares this typed field so the surrounding contract is explicit.
    user_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> dict[str, bool]:
    # Performs this required operation before the surrounding flow continues.
    await _admin_limit(request, principal, "admin.profile.moderate", user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if user_id == principal.user_id:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(409, "ADMIN_SELF_MODERATION_FORBIDDEN", "Use another administrator.")
    # Stores `profile` because later steps depend on this value.
    profile = await session.get(Profile, user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if profile is None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(404, "PROFILE_NOT_FOUND", "Profile not found.")
    # Guards the nested operation so it runs only when this condition is satisfied.
    if payload.enabled is not None:
        # Stores `profile.is_banned` because later steps depend on this value.
        profile.is_banned = payload.enabled
    # Guards the nested operation so it runs only when this condition is satisfied.
    if payload.display_name is not None:
        # Stores `safe_name` because later steps depend on this value.
        safe_name = ProfileUpdateRequest(display_name=payload.display_name).display_name
        # Stores `profile.display_name` because later steps depend on this value.
        profile.display_name = safe_name
        # Stores `profile.normalized_display_name` because later steps depend on this value.
        profile.normalized_display_name = normalize_display_name(safe_name or "") or None
    # Supplies this required nested value.
    session.add(
        # Supplies this required nested value.
        ModerationAction(
            # Stores `actor_id` because later steps depend on this value.
            actor_id=principal.user_id,
            # Stores `target_user_id` because later steps depend on this value.
            target_user_id=user_id,
            # Stores `action` because later steps depend on this value.
            action="ban" if profile.is_banned else "unban_or_rename",
            # Stores `reason` because later steps depend on this value.
            reason=payload.reason,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Supplies this required nested value.
    audit(session, principal, "profile.moderated", "profile", user_id, payload.reason)
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Performs this required operation before the surrounding flow continues.
    await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns the computed result and ends the current callable.
    return {"updated": True}


# Applies this decorator to configure the declaration immediately below.
@router.post("/challenges/{challenge_id}/revoke")
# Defines this callable to implement the operation described by its name.
async def admin_revoke_challenge_route(
    # Declares this typed field so the surrounding contract is explicit.
    challenge_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> dict[str, bool]:
    # Performs this required operation before the surrounding flow continues.
    await _admin_limit(request, principal, "admin.challenge.revoke", challenge_id)
    # Stores `challenge` because later steps depend on this value.
    challenge = await session.get(FriendChallenge, challenge_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if challenge is None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    # Stores `challenge.revoked_at` because later steps depend on this value.
    challenge.revoked_at = utcnow()
    # Supplies this required nested value.
    audit(session, principal, "challenge.revoked", "friend_challenge", challenge_id, payload.reason)
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Returns the computed result and ends the current callable.
    return {"revoked": True}


# Applies this decorator to configure the declaration immediately below.
@router.post("/rooms/{room_id}/terminate")
# Defines this callable to implement the operation described by its name.
async def terminate_room_route(
    # Declares this typed field so the surrounding contract is explicit.
    room_id: uuid.UUID,
    # Declares this typed field so the surrounding contract is explicit.
    payload: AdminActionRequest,
    # Declares this typed field so the surrounding contract is explicit.
    request: Request,
    # Stores `principal` because later steps depend on this value.
    principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> dict[str, bool]:
    # Performs this required operation before the surrounding flow continues.
    await _admin_limit(request, principal, "admin.room.terminate", room_id)
    # Stores `room` because later steps depend on this value.
    room = await session.get(MultiplayerRoom, room_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if room is None:
        # Raises this error so invalid state cannot continue silently.
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found.")
    # Stores `room.status` because later steps depend on this value.
    room.status = "terminated"
    # Supplies this required nested value.
    audit(session, principal, "room.terminated", "multiplayer_room", room_id, payload.reason)
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Returns the computed result and ends the current callable.
    return {"terminated": True}


# Applies this decorator to configure the declaration immediately below.
@router.get("/audit", response_model=list[AuditEventResponse])
# Defines this callable to implement the operation described by its name.
async def audit_route(
    # Stores `limit` because later steps depend on this value.
    limit: int = Query(default=100, ge=1, le=250),
    # Stores `_principal` because later steps depend on this value.
    _principal: AuthPrincipal = Depends(require_admin),
    # Stores `session` because later steps depend on this value.
    session: MongoSession = Depends(get_session),
    # Closes the multiline declaration, call, or collection opened above.
) -> list[AuditEventResponse]:
    # Stores `events` because later steps depend on this value.
    events = await session.find_many(
        # Supplies this required nested value.
        AuditEvent,
        sort=[("created_at", DESCENDING)],
        limit=limit,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Returns the computed result and ends the current callable.
    return [
        # Supplies this required nested value.
        AuditEventResponse(
            # Stores `id` because later steps depend on this value.
            id=event.id,
            # Stores `actor_id` because later steps depend on this value.
            actor_id=event.actor_id,
            # Stores `action` because later steps depend on this value.
            action=event.action,
            # Stores `target_type` because later steps depend on this value.
            target_type=event.target_type,
            # Stores `target_id` because later steps depend on this value.
            target_id=event.target_id,
            # Stores `reason` because later steps depend on this value.
            reason=event.reason,
            # Stores `created_at` because later steps depend on this value.
            created_at=event.created_at,
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Iterates over these values so each item receives the same processing.
        for event in events
        # Closes the multiline declaration, call, or collection opened above.
    ]
