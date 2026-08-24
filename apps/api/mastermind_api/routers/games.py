# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `contextlib` for use in this module.
from contextlib import suppress

# Imports selected names from `fastapi` for use in this module.
from fastapi import APIRouter, Depends, Request, status

# Imports selected names from `redis.exceptions` for use in this module.
from redis.exceptions import RedisError

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession

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

# Imports selected names from `..rate_limit` for use in this module.
from ..rate_limit import enforce_action_limit

# Imports selected names from `..realtime` for use in this module.
from ..realtime import Broker

# Imports selected names from `..retention` for use in this module.
from ..retention import expire_game_record

# Imports selected names from `..schemas` for use in this module.
from ..schemas import AttemptRequest, CreateGameRequest, GameResponse

# Imports selected names from `..services` for use in this module.
from ..services import abandon, create_game, game_response, load_owned_game, submit_attempt, utcnow

# Computes and stores `router` for subsequent operations.
router = APIRouter(prefix="/v1/games", tags=["games"])


# Applies `@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)` to
# configure the declaration immediately below.
@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
# Defines the `create_game_route` callable and its typed interface.
async def create_game_route(
    # Declares the typed `payload` data field.
    payload: CreateGameRequest,
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
) -> GameResponse:
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="game.create",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `weight` parameter or keyword argument.
        weight=4,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=payload.mode.value == "solo" and payload.difficulty is not None,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game` for subsequent operations.
    game = await create_game(session, principal, payload, cipher, settings=settings)
    # Returns this result to the caller and ends the current function.
    return game_response(game, cipher)


# Applies `@router.get("/{game_id}", response_model=GameResponse)` to configure the declaration
# immediately below.
@router.get("/{game_id}", response_model=GameResponse)
# Defines the `get_game_route` callable and its typed interface.
async def get_game_route(
    # Declares the typed `game_id` data field.
    game_id: str,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> GameResponse:
    # Computes and stores `game` for subsequent operations.
    game = await load_owned_game(session, game_id, principal, for_update=True)
    # Checks this condition before executing the nested branch.
    if expire_game_record(game, now=utcnow()):
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Returns this result to the caller and ends the current function.
    return game_response(game, cipher)


# Applies `@router.post("/{game_id}/attempts", response_model=GameResponse)` to configure the
# declaration immediately below.
@router.post("/{game_id}/attempts", response_model=GameResponse)
# Defines the `submit_attempt_route` callable and its typed interface.
async def submit_attempt_route(
    # Declares the typed `game_id` data field.
    game_id: str,
    # Declares the typed `payload` data field.
    payload: AttemptRequest,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> GameResponse:
    # Computes and stores `existing` for subsequent operations.
    existing = await load_owned_game(session, game_id, principal)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="game.attempt",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=existing.id,
        # Provides the `weight` parameter or keyword argument.
        weight=2,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=existing.ranked_eligibility == "eligible",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game` for subsequent operations.
    game = await submit_attempt(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        game_id,
        # Supplies this item to the surrounding call or collection.
        payload.guess,
        # Supplies this item to the surrounding call or collection.
        payload.idempotency_key,
        # Uses the current HTTP request or response in this operation.
        request.state.request_id,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if game.status in {"won", "lost"} and game.ranked_eligibility == "eligible":
        # Waits for this asynchronous operation to complete.
        await invalidate_leaderboard_cache(request.app.state.redis)
    # Returns this result to the caller and ends the current function.
    return game_response(game, cipher)


# Applies `@router.post("/{game_id}/abandon", response_model=GameResponse)` to configure the
# declaration immediately below.
@router.post("/{game_id}/abandon", response_model=GameResponse)
# Defines the `abandon_game_route` callable and its typed interface.
async def abandon_game_route(
    # Declares the typed `game_id` data field.
    game_id: str,
    # Declares the typed `request` data field.
    request: Request,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal = Depends(get_current_user),
    # Provides the `session` parameter or keyword argument.
    session: AsyncSession = Depends(get_session),
    # Provides the `cipher` parameter or keyword argument.
    cipher: SecretCipher = Depends(get_cipher),
    # Completes the signature and declares the callable return type.
) -> GameResponse:
    # Computes and stores `existing` for subsequent operations.
    existing = await load_owned_game(session, game_id, principal)
    # Waits for this asynchronous operation to complete.
    await enforce_action_limit(
        # Supplies this item to the surrounding call or collection.
        request,
        # Provides the `action` parameter or keyword argument.
        action="game.abandon",
        # Provides the `subject` parameter or keyword argument.
        subject=principal.user_id,
        # Provides the `resource` parameter or keyword argument.
        resource=existing.id,
        # Provides the `weight` parameter or keyword argument.
        weight=4,
        # Provides the `integrity_required` parameter or keyword argument.
        integrity_required=existing.ranked_eligibility == "eligible",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `room_events` for subsequent operations.
    room_events: list[tuple[str, dict[str, object]]] = []
    # Computes and stores `response` for subsequent operations.
    response = await abandon(session, principal, game_id, cipher, room_events=room_events)
    # Computes and stores `broker` for subsequent operations.
    broker: Broker = request.app.state.broker
    # Iterates through the supplied values for the nested operation.
    for room_id, event in room_events:
        # Acquires this managed resource and guarantees cleanup afterward.
        with suppress(RedisError, RuntimeError):
            # Waits for this asynchronous operation to complete.
            await broker.publish(room_id, event)
    # Returns this result to the caller and ends the current function.
    return response
