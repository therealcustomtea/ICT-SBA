# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Query, Request, Response, status

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import case, func, select

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

# Imports selected names from `..auth` for use in this module.
from ..auth import AuthPrincipal, get_current_user

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

# Imports selected names from `..models` for use in this module.
from ..models import FriendChallenge, GameSession

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import enforce_action_limit

# Imports selected names from `..schemas` for use in this module.
from ..schemas import (
    # Supplies this item to the surrounding call or collection.
    ChallengeResponse,
    # Supplies this item to the surrounding call or collection.
    ChallengeResultItem,
    # Supplies this item to the surrounding call or collection.
    ChallengeResultsResponse,
    # Supplies this item to the surrounding call or collection.
    CreateChallengeRequest,
    # Supplies this item to the surrounding call or collection.
    GameConfigSchema,
    # Supplies this item to the surrounding call or collection.
    GameResponse,
    # Supplies this item to the surrounding call or collection.
    OwnedChallengeItem,
    # Supplies this item to the surrounding call or collection.
    PaginatedOwnedChallenges,
    # Supplies this item to the surrounding call or collection.
    StartGameRequest,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `..services` for use in this module.
from ..services import (
    # Supplies this item to the surrounding call or collection.
    challenge_response,
    # Supplies this item to the surrounding call or collection.
    create_challenge,
    # Supplies this item to the surrounding call or collection.
    game_response,
    # Supplies this item to the surrounding call or collection.
    load_challenge,
    # Supplies this item to the surrounding call or collection.
    start_challenge,
    # Supplies this item to the surrounding call or collection.
    utcnow,
    # Closes the multiline call, declaration, or collection started above.
)

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/challenges", tags=["friend challenges"])


# Defines the `require_challenges` callable and its typed interface.
async def require_challenges(session: AsyncSession, settings: Settings) -> None:
    # Checks this condition before executing the nested branch.
    if not await feature_enabled(session, settings, "friend_challenges"):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "FEATURE_DISABLED", "Friend challenges are temporarily unavailable.")


# Applies `@router.get("/{challenge_id}/results", response_model=ChallengeResultsResponse)` to
# configure the declaration immediately below.
@router.get("/{challenge_id}/results", response_model=ChallengeResultsResponse)
# Defines the `challenge_results_route` callable and its typed interface.
async def challenge_results_route(
    # Declares the typed `challenge_id` data field.
    challenge_id: uuid.UUID,
    # Provides the `page` parameter or keyword argument.
    page: int = 1,
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = 25,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> ChallengeResultsResponse:
    # Waits for this asynchronous operation to complete.
    await require_challenges(session, settings)
    # Checks this condition before executing the nested branch.
    if page < 1 or not 1 <= page_size <= 100:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(422, "INVALID_PAGE", "Use a positive page and a page size up to 100.")
    # Computes and stores `challenge` for subsequent operations.
    challenge = await session.scalar(
        # Calls `select` with the supplied values.
        select(FriendChallenge).where(
            # Supplies this item to the surrounding call or collection.
            FriendChallenge.id == challenge_id,
            # Supplies this item to the surrounding call or collection.
            FriendChallenge.creator_id == principal.user_id,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if challenge is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    # Computes and stores `base` for subsequent operations.
    base = select(GameSession).where(
        # Supplies this item to the surrounding call or collection.
        GameSession.friend_challenge_id == challenge.id,
        # Calls `GameSession.completed_at.is_not` with the supplied values.
        GameSession.completed_at.is_not(None),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `total` for subsequent operations.
    total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
    # Computes and stores `aggregate` for subsequent operations.
    aggregate = await session.execute(
        # Calls `select` with the supplied values.
        select(
            # Calls `func.sum` with the supplied values.
            func.sum(case((GameSession.status == "won", 1), else_=0)),
            # Calls `func.avg` with the supplied values.
            func.avg(GameSession.attempts_used),
            # Begins the nested block or multiline expression completed below.
        ).where(
            # Supplies this item to the surrounding call or collection.
            GameSession.friend_challenge_id == challenge.id,
            # Calls `GameSession.completed_at.is_not` with the supplied values.
            GameSession.completed_at.is_not(None),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Executes this statement as the next step in the surrounding logic.
    wins, average = aggregate.one()
    # Computes and stores `results` for subsequent operations.
    results = (
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `base.order_by` with the supplied values.
            base.order_by(
                # Calls `func.coalesce` with the supplied values.
                func.coalesce(GameSession.final_score, 0).desc(),
                # Calls `GameSession.attempts_used.asc` with the supplied values.
                GameSession.attempts_used.asc(),
                # Calls `GameSession.elapsed_seconds.asc` with the supplied values.
                GameSession.elapsed_seconds.asc().nulls_last(),
                # Calls `GameSession.completed_at.asc` with the supplied values.
                GameSession.completed_at.asc(),
                # Calls `GameSession.public_id.asc` with the supplied values.
                GameSession.public_id.asc(),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Computes and stores `all_scores` for subsequent operations.
    all_scores = list(
        # Waits for this asynchronous operation to complete.
        await session.scalars(
            # Calls `select` with the supplied values.
            select(GameSession.final_score).where(
                # Supplies this item to the surrounding call or collection.
                GameSession.friend_challenge_id == challenge.id,
                # Calls `GameSession.completed_at.is_not` with the supplied values.
                GameSession.completed_at.is_not(None),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `distribution` for subsequent operations.
    distribution = {"zero": 0, "1-999": 0, "1000-1499": 0, "1500+": 0}
    # Iterates through the supplied values for the nested operation.
    for score in all_scores:
        # Computes and stores `value` for subsequent operations.
        value = score or 0
        # Computes and stores `bucket` for subsequent operations.
        bucket = (
            # Executes this statement as the next step in the surrounding logic.
            "zero"
            # Checks this condition before executing the nested branch.
            if value == 0
            # Executes this statement as the next step in the surrounding logic.
            else "1-999"
            # Checks this condition before executing the nested branch.
            if value < 1000
            # Executes this statement as the next step in the surrounding logic.
            else "1000-1499"
            # Checks this condition before executing the nested branch.
            if value < 1500
            # Executes this statement as the next step in the surrounding logic.
            else "1500+"
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
        distribution[bucket] += 1
    # Returns this result to the caller and ends the current function.
    return ChallengeResultsResponse(
        # Provides the `completed_count` parameter or keyword argument.
        completed_count=total,
        # Provides the `win_rate` parameter or keyword argument.
        win_rate=round((wins or 0) / total * 100, 1) if total else 0.0,
        # Provides the `average_attempts` parameter or keyword argument.
        average_attempts=round(float(average), 2) if average is not None else None,
        # Provides the `score_distribution` parameter or keyword argument.
        score_distribution=distribution,
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `ChallengeResultItem` with the supplied values.
            ChallengeResultItem(
                # Provides the `rank` parameter or keyword argument.
                rank=(page - 1) * page_size + index,
                # Provides the `player_label` parameter or keyword argument.
                player_label=f"Breaker {game.public_id[:6].upper()}",
                # Provides the `result` parameter or keyword argument.
                result=game.status,
                # Provides the `attempts_used` parameter or keyword argument.
                attempts_used=game.attempts_used,
                # Provides the `max_attempts` parameter or keyword argument.
                max_attempts=game.maximum_attempts,
                # Provides the `score` parameter or keyword argument.
                score=game.final_score or 0,
                # Provides the `elapsed_seconds` parameter or keyword argument.
                elapsed_seconds=game.elapsed_seconds,
                # Provides the `completed_at` parameter or keyword argument.
                completed_at=game.completed_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for index, game in enumerate(results, start=1)
            # Checks this condition before executing the nested branch.
            if game.completed_at is not None
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


# Applies `@router.post("", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)`
# to configure the declaration immediately below.
@router.post("", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
# Defines the `create_challenge_route` callable and its typed interface.
async def create_challenge_route(
    # Declares the typed `payload` data field.
    payload: CreateChallengeRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> ChallengeResponse:
    # Waits for this asynchronous operation to complete.
    await require_challenges(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="challenge.create",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=10,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Executes this statement as the next step in the surrounding logic.
    challenge, share_code = await create_challenge(session, principal, payload, cipher, settings)
    # Returns this result to the caller and ends the current function.
    return await challenge_response(session, challenge, principal, share_code)


# Applies `@router.get("/mine", response_model=PaginatedOwnedChallenges)` to configure the
# declaration immediately below.
@router.get("/mine", response_model=PaginatedOwnedChallenges)
# Defines the `owned_challenges_route` callable and its typed interface.
async def owned_challenges_route(
    # Provides the `page` parameter or keyword argument.
    page: int = Query(default=1, ge=1),
    # Provides the `page_size` parameter or keyword argument.
    page_size: int = Query(default=20, ge=1, le=100),
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> PaginatedOwnedChallenges:
    # Waits for this asynchronous operation to complete.
    await require_challenges(session, settings)
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
    # Computes and stores `base` for subsequent operations.
    base = select(FriendChallenge, completed_count.label("completed_count")).where(
        # Executes this statement as the next step in the surrounding logic.
        FriendChallenge.creator_id == principal.user_id
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `total` for subsequent operations.
    total = (
        # Waits for this asynchronous operation to complete.
        await session.scalar(
            # Calls `select` with the supplied values.
            select(func.count()).select_from(
                # Calls `select` with the supplied values.
                select(FriendChallenge.id)
                # Executes this statement as the next step in the surrounding logic.
                .where(FriendChallenge.creator_id == principal.user_id)
                # Executes this statement as the next step in the surrounding logic.
                .subquery()
                # Closes the multiline call, declaration, or collection started above.
            )
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
            # Calls `base.order_by` with the supplied values.
            base.order_by(FriendChallenge.created_at.desc(), FriendChallenge.id)
            # Executes this statement as the next step in the surrounding logic.
            .offset((page - 1) * page_size)
            # Executes this statement as the next step in the surrounding logic.
            .limit(page_size)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Executes this statement as the next step in the surrounding logic.
    ).all()
    # Returns this result to the caller and ends the current function.
    return PaginatedOwnedChallenges(
        # Computes and stores `items` for subsequent operations.
        items=[
            # Calls `OwnedChallengeItem` with the supplied values.
            OwnedChallengeItem(
                # Provides the `id` parameter or keyword argument.
                id=challenge.id,
                # Provides the `title` parameter or keyword argument.
                title=challenge.title,
                # Provides the `show_creator_name` parameter or keyword argument.
                show_creator_name=challenge.show_creator_name,
                # Provides the `config` parameter or keyword argument.
                config=GameConfigSchema.model_validate(challenge.config),
                # Provides the `revoked` parameter or keyword argument.
                revoked=challenge.revoked_at is not None,
                # Provides the `expires_at` parameter or keyword argument.
                expires_at=challenge.expires_at,
                # Provides the `completed_count` parameter or keyword argument.
                completed_count=count,
                # Provides the `created_at` parameter or keyword argument.
                created_at=challenge.created_at,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Iterates through the supplied values for the nested operation.
            for challenge, count in rows
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


# Applies `@router.get("/{share_code}", response_model=ChallengeResponse)` to configure the
# declaration immediately below.
@router.get("/{share_code}", response_model=ChallengeResponse)
# Defines the `get_challenge_route` callable and its typed interface.
async def get_challenge_route(
    # Declares the typed `share_code` data field.
    share_code: str,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> ChallengeResponse:
    # Waits for this asynchronous operation to complete.
    await require_challenges(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="challenge.lookup",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=share_code,
        # Provides the `weight` parameter or keyword argument.
        weight=2,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `challenge` for subsequent operations.
    challenge = await load_challenge(session, share_code, settings)
    # Returns this result to the caller and ends the current function.
    return await challenge_response(session, challenge, principal, share_code)


# Applies `@router.post("/{share_code}/start", response_model=GameResponse)` to configure the
# declaration immediately below.
@router.post("/{share_code}/start", response_model=GameResponse)
# Defines the `start_challenge_route` callable and its typed interface.
async def start_challenge_route(
    # Declares the typed `share_code` data field.
    share_code: str,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `payload` parameter or keyword argument.
    payload: StartGameRequest | None = None,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> GameResponse:
    # Waits for this asynchronous operation to complete.
    await require_challenges(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="challenge.start",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=share_code,
        # Provides the `weight` parameter or keyword argument.
        weight=6,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `challenge` for subsequent operations.
    challenge = await load_challenge(session, share_code, settings)
    # Computes and stores `game` for subsequent operations.
    game = await start_challenge(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        challenge,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `practice` parameter or keyword argument.
        practice=bool(payload and payload.practice),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return game_response(game, cipher)


# Applies `@router.delete(` to configure the declaration immediately below.
@router.delete(
    # Supplies this item to the surrounding call or collection.
    "/{challenge_id}",
    # Provides the `status_code` parameter or keyword argument.
    status_code=status.HTTP_204_NO_CONTENT,
    # Provides the `response_class` parameter or keyword argument.
    response_class=Response,
    # Provides the `response_model` parameter or keyword argument.
    response_model=None,
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `revoke_challenge_route` callable and its typed interface.
async def revoke_challenge_route(
    # Declares the typed `challenge_id` data field.
    challenge_id: uuid.UUID,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `settings` parameter or keyword argument.
    settings: Settings = Depends(get_settings),
    # Completes the signature and declares the callable return type.
) -> None:
    # Waits for this asynchronous operation to complete.
    await require_challenges(session, settings)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="challenge.revoke",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=challenge_id,
        # Provides the `weight` parameter or keyword argument.
        weight=8,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `challenge` for subsequent operations.
    challenge = await session.scalar(
        # Calls `select` with the supplied values.
        select(FriendChallenge).where(
            # Supplies this item to the surrounding call or collection.
            FriendChallenge.id == challenge_id,
            # Supplies this item to the surrounding call or collection.
            FriendChallenge.creator_id == principal.user_id,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if challenge is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    # Checks this condition before executing the nested branch.
    if challenge.revoked_at is None:
        # Computes and stores `challenge.revoked_at` for subsequent operations.
        challenge.revoked_at = utcnow()
        # Waits for this asynchronous operation to complete.
        await session.commit()
