from __future__ import annotations

from contextlib import suppress

from fastapi import APIRouter, Depends, Request, status
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import AuthPrincipal, get_current_user
from ..cache import invalidate_leaderboard_cache
from ..config import Settings, get_settings
from ..crypto import SecretCipher
from ..database import get_session
from ..dependencies import get_cipher
from ..rate_limit import enforce_action_limit
from ..realtime import Broker
from ..retention import expire_game_record
from ..schemas import AttemptRequest, CreateGameRequest, GameResponse
from ..services import abandon, create_game, game_response, load_owned_game, submit_attempt, utcnow

router = APIRouter(prefix="/v1/games", tags=["games"])


@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game_route(
    payload: CreateGameRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
    settings: Settings = Depends(get_settings),
) -> GameResponse:
    await enforce_action_limit(
        request,
        action="game.create",
        subject=principal.user_id,
        weight=4,
        integrity_required=payload.mode.value == "solo" and payload.difficulty is not None,
    )
    game = await create_game(session, principal, payload, cipher, settings=settings)
    return game_response(game, cipher)


@router.get("/{game_id}", response_model=GameResponse)
async def get_game_route(
    game_id: str,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
) -> GameResponse:
    game = await load_owned_game(session, game_id, principal, for_update=True)
    if expire_game_record(game, now=utcnow()):
        await session.commit()
    return game_response(game, cipher)


@router.post("/{game_id}/attempts", response_model=GameResponse)
async def submit_attempt_route(
    game_id: str,
    payload: AttemptRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
) -> GameResponse:
    existing = await load_owned_game(session, game_id, principal)
    await enforce_action_limit(
        request,
        action="game.attempt",
        subject=principal.user_id,
        resource=existing.id,
        weight=2,
        integrity_required=existing.ranked_eligibility == "eligible",
    )
    game = await submit_attempt(
        session,
        principal,
        game_id,
        payload.guess,
        payload.idempotency_key,
        request.state.request_id,
        cipher,
    )
    if game.status in {"won", "lost"} and game.ranked_eligibility == "eligible":
        await invalidate_leaderboard_cache(request.app.state.redis)
    return game_response(game, cipher)


@router.post("/{game_id}/abandon", response_model=GameResponse)
async def abandon_game_route(
    game_id: str,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    cipher: SecretCipher = Depends(get_cipher),
) -> GameResponse:
    existing = await load_owned_game(session, game_id, principal)
    await enforce_action_limit(
        request,
        action="game.abandon",
        subject=principal.user_id,
        resource=existing.id,
        weight=4,
        integrity_required=existing.ranked_eligibility == "eligible",
    )
    room_events: list[tuple[str, dict[str, object]]] = []
    response = await abandon(session, principal, game_id, cipher, room_events=room_events)
    broker: Broker = request.app.state.broker
    for room_id, event in room_events:
        with suppress(RedisError, RuntimeError):
            await broker.publish(room_id, event)
    return response
