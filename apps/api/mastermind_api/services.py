from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import secrets
import unicodedata
import uuid
import zipfile
from datetime import UTC, date, datetime, timedelta

from mastermind_core import (
    DAILY_DERIVATION_VERSION,
    RULE_SET_VERSION,
    SCORING_VERSION,
    CodeMakerType,
    DomainError,
    GameConfig,
    GameMode,
    GameStatus,
    LeaderboardEligibility,
    calculate_feedback,
    calculate_score,
    daily_challenge_id,
    derive_daily_secret,
    generate_secret,
    get_preset,
    preset_name,
    validate_code,
)
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .auth import AuthPrincipal
from .config import Settings, get_settings
from .crypto import SecretCipher
from .errors import APIError
from .features import feature_enabled
from .models import (
    AdminGrant,
    AuditEvent,
    DailyChallenge,
    FriendChallenge,
    GameAttempt,
    GameSession,
    LeaderboardEntry,
    MultiplayerMember,
    MultiplayerRoom,
    Profile,
    SupportRequest,
    UserAchievement,
)
from .realtime import (
    record_room_completion,
    record_room_event,
)
from .retention import expire_game_record, game_expiry_for_mode
from .schemas import (
    AttemptSchema,
    ChallengeResponse,
    CreateChallengeRequest,
    CreateGameRequest,
    FeedbackSchema,
    GameConfigSchema,
    GameResponse,
    ProfileResponse,
    RoomMemberResponse,
    RoomResponse,
    ScoreBreakdownSchema,
)

OFFICIAL_GAME_MODES = {GameMode.SOLO, GameMode.DAILY}
MAX_ACTIVE_CHALLENGES_PER_USER = 25
MAX_ACTIVE_GUEST_CHALLENGES = 3


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def public_token(bytes_count: int = 16) -> str:
    return secrets.token_urlsafe(bytes_count).rstrip("=")


def identifier_hash(value: str, settings: Settings) -> str:
    key = settings.public_identifier_hmac_key.encode()
    if len(key) < 32:
        raise APIError(503, "INVITES_UNAVAILABLE", "Private invites are temporarily unavailable.")
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def idempotent_invite_code(
    namespace: str,
    user_id: uuid.UUID,
    idempotency_key: str,
    settings: Settings,
) -> str:
    key = settings.public_identifier_hmac_key.encode()
    if len(key) < 32:
        raise APIError(503, "INVITES_UNAVAILABLE", "Private invites are temporarily unavailable.")
    digest = hmac.new(
        key,
        f"{namespace}|{user_id}|{idempotency_key}".encode(),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def creation_request_fingerprint(
    operation: str,
    payload: dict[str, object],
    settings: Settings,
) -> str:
    key = settings.public_identifier_hmac_key.encode()
    if len(key) < 32:
        raise APIError(503, "IDEMPOTENCY_UNAVAILABLE", "Safe request retries are unavailable.")
    canonical = json.dumps(
        {"operation": operation, "payload": payload},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


def config_from_schema(schema: GameConfigSchema) -> GameConfig:
    return GameConfig(
        colours=tuple(schema.colours),
        code_length=schema.code_length,
        max_attempts=schema.max_attempts,
        duplicates_allowed=schema.duplicates_allowed,
        code_maker=schema.code_maker,
        visibility=schema.visibility,
        ranked=False,
        time_bonus_cap=schema.time_bonus_cap,
    )


def resolve_config(
    difficulty: str | None,
    custom: GameConfigSchema | None,
) -> tuple[GameConfig, str | None]:
    if difficulty:
        return get_preset(difficulty), difficulty
    if custom:
        return config_from_schema(custom), None
    raise DomainError("MISSING_GAME_CONFIG", "Choose a difficulty or custom game settings.")


async def ensure_profile(session: AsyncSession, principal: AuthPrincipal) -> Profile:
    profile = await session.get(Profile, principal.user_id)
    if profile is None:
        profile = Profile(id=principal.user_id, is_anonymous=principal.is_anonymous)
        session.add(profile)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            profile = await session.get(Profile, principal.user_id)
            if profile is None:
                raise
    elif profile.deleted_at is not None:
        raise APIError(403, "ACCOUNT_DELETED", "This account has been deleted.")
    if profile.is_banned:
        raise APIError(403, "ACCOUNT_RESTRICTED", "This account is restricted.")
    if profile.is_anonymous and not principal.is_anonymous:
        profile.is_anonymous = False
    return profile


def _cipher_context(public_id: str) -> str:
    return f"game:{public_id}:{RULE_SET_VERSION}"


def _idempotency_reused() -> APIError:
    return APIError(
        409,
        "IDEMPOTENCY_KEY_REUSED",
        "This idempotency key was already used with a different request.",
    )


def _expected_game_config(request: CreateGameRequest) -> tuple[GameConfig, str | None]:
    config, difficulty = resolve_config(request.difficulty, request.config)
    if request.mode in {GameMode.PRACTICE, GameMode.PASS_AND_PLAY}:
        config = GameConfig.from_dict(config.to_dict() | {"ranked": False})
    return config, difficulty


def _game_creation_matches(
    game: GameSession,
    request: CreateGameRequest,
    cipher: SecretCipher,
    *,
    daily_id: uuid.UUID | None,
    friend_id: uuid.UUID | None,
    room_id: uuid.UUID | None,
) -> bool:
    config, difficulty = _expected_game_config(request)
    if (
        game.mode != request.mode.value
        or game.difficulty != difficulty
        or game.config != config.to_dict()
        or game.daily_challenge_id != daily_id
        or game.friend_challenge_id != friend_id
        or game.room_id != room_id
    ):
        return False
    if request.secret is None:
        return True
    requested_secret = validate_code(request.secret, config)
    stored_secret = cipher.decrypt(
        game.encrypted_secret,
        game.secret_nonce,
        game.secret_key_version,
        context=_cipher_context(game.public_id),
    )
    return stored_secret == requested_secret


def _assert_game_creation_matches(
    game: GameSession,
    request: CreateGameRequest,
    cipher: SecretCipher,
    *,
    daily_id: uuid.UUID | None,
    friend_id: uuid.UUID | None,
    room_id: uuid.UUID | None,
) -> None:
    if not _game_creation_matches(
        game,
        request,
        cipher,
        daily_id=daily_id,
        friend_id=friend_id,
        room_id=room_id,
    ):
        raise _idempotency_reused()


async def load_owned_game(
    session: AsyncSession,
    public_id: str,
    principal: AuthPrincipal,
    *,
    for_update: bool = False,
) -> GameSession:
    await ensure_profile(session, principal)
    query = (
        select(GameSession)
        .options(selectinload(GameSession.attempts))
        .where(GameSession.public_id == public_id, GameSession.owner_id == principal.user_id)
    )
    if for_update:
        query = query.with_for_update()
    game = await session.scalar(query)
    if game is None:
        raise APIError(404, "GAME_NOT_FOUND", "Game not found.")
    return game


def game_response(game: GameSession, cipher: SecretCipher) -> GameResponse:
    terminal = GameStatus(game.status).terminal and game.mode != GameMode.DUEL.value
    secret = None
    if terminal:
        secret = list(
            cipher.decrypt(
                game.encrypted_secret,
                game.secret_nonce,
                game.secret_key_version,
                context=_cipher_context(game.public_id),
            )
        )
    attempts = [
        AttemptSchema(
            number=attempt.attempt_number,
            guess=attempt.guess,
            feedback=FeedbackSchema(black=attempt.black_pegs, white=attempt.white_pegs),
            submitted_at=attempt.submitted_at,
        )
        for attempt in game.attempts
    ]
    breakdown = (
        ScoreBreakdownSchema.model_validate(game.score_breakdown) if game.score_breakdown else None
    )
    return GameResponse(
        id=game.public_id,
        mode=game.mode,
        status=game.status,
        difficulty=game.difficulty,
        config=GameConfigSchema.model_validate(game.config),
        attempts=attempts,
        attempts_used=game.attempts_used,
        max_attempts=game.maximum_attempts,
        attempts_remaining=max(0, game.maximum_attempts - game.attempts_used),
        started_at=game.started_at,
        completed_at=game.completed_at,
        score=game.final_score,
        score_breakdown=breakdown,
        secret=secret,
        ranked=game.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value,
    )


async def create_game(
    session: AsyncSession,
    principal: AuthPrincipal,
    request: CreateGameRequest,
    cipher: SecretCipher,
    *,
    secret_override: tuple[str, ...] | None = None,
    daily_id: uuid.UUID | None = None,
    friend_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
    linked_expires_at: datetime | None = None,
    commit: bool = True,
    settings: Settings | None = None,
) -> GameSession:
    await ensure_profile(session, principal)
    fingerprint = None
    if request.idempotency_key:
        fingerprint = creation_request_fingerprint(
            "game.create",
            request.model_dump(mode="json", by_alias=True, exclude={"idempotency_key"})
            | {
                "dailyId": str(daily_id) if daily_id else None,
                "friendId": str(friend_id) if friend_id else None,
                "roomId": str(room_id) if room_id else None,
            },
            settings or get_settings(),
        )
        existing = await session.scalar(
            select(GameSession)
            .options(selectinload(GameSession.attempts))
            .where(
                GameSession.owner_id == principal.user_id,
                GameSession.creation_idempotency_key == request.idempotency_key,
            )
        )
        if existing:
            if (
                existing.creation_request_fingerprint is not None
                and existing.creation_request_fingerprint != fingerprint
            ):
                raise _idempotency_reused()
            _assert_game_creation_matches(
                existing,
                request,
                cipher,
                daily_id=daily_id,
                friend_id=friend_id,
                room_id=room_id,
            )
            return existing
    if request.mode in {GameMode.DAILY, GameMode.FRIEND_CHALLENGE, GameMode.DUEL} and not (
        daily_id or friend_id or room_id
    ):
        raise APIError(
            400, "DEDICATED_ENDPOINT_REQUIRED", "Use the dedicated endpoint for this mode."
        )
    config, difficulty = _expected_game_config(request)
    if (
        config.code_maker is CodeMakerType.HUMAN
        and request.mode is not GameMode.PASS_AND_PLAY
        and friend_id is None
        and secret_override is None
    ):
        raise APIError(400, "INVALID_CODE_MAKER", "Human Code Maker is available in pass-and-play.")
    if request.secret is not None:
        if config.code_maker is not CodeMakerType.HUMAN and not friend_id:
            raise APIError(
                400, "SECRET_NOT_ACCEPTED", "A secret is not accepted for this game mode."
            )
        secret_code = validate_code(request.secret, config)
    else:
        secret_code = secret_override or generate_secret(config)
    public_id = public_token()
    encrypted = cipher.encrypt(secret_code, context=_cipher_context(public_id))
    started_at = utcnow()
    ranked = (
        config.ranked
        and request.mode in OFFICIAL_GAME_MODES
        and difficulty is not None
        and preset_name(config) == difficulty
    )
    game = GameSession(
        public_id=public_id,
        creation_idempotency_key=request.idempotency_key,
        creation_request_fingerprint=fingerprint,
        owner_id=principal.user_id,
        mode=request.mode.value,
        difficulty=difficulty,
        config=config.to_dict(),
        status=GameStatus.ACTIVE.value,
        rule_set_version=RULE_SET_VERSION,
        scoring_version=SCORING_VERSION,
        encrypted_secret=encrypted.ciphertext,
        secret_nonce=encrypted.nonce,
        secret_key_version=encrypted.key_version,
        attempts_used=0,
        maximum_attempts=config.max_attempts,
        started_at=started_at,
        expires_at=game_expiry_for_mode(
            request.mode,
            started_at,
            linked_expires_at=linked_expires_at,
        ),
        ranked_eligibility=(
            LeaderboardEligibility.ELIGIBLE.value
            if ranked
            else LeaderboardEligibility.UNRANKED.value
        ),
        daily_challenge_id=daily_id,
        friend_challenge_id=friend_id,
        room_id=room_id,
        attempts=[],
    )
    session.add(game)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        identity_filter = None
        if request.idempotency_key:
            identity_filter = GameSession.creation_idempotency_key == request.idempotency_key
        elif daily_id is not None:
            identity_filter = GameSession.daily_challenge_id == daily_id
        elif friend_id is not None:
            identity_filter = GameSession.friend_challenge_id == friend_id
        elif room_id is not None:
            identity_filter = GameSession.room_id == room_id
        if identity_filter is not None:
            concurrent_game = await session.scalar(
                select(GameSession)
                .options(selectinload(GameSession.attempts))
                .where(GameSession.owner_id == principal.user_id, identity_filter)
            )
            if concurrent_game:
                if request.idempotency_key:
                    if (
                        concurrent_game.creation_request_fingerprint is not None
                        and concurrent_game.creation_request_fingerprint != fingerprint
                    ):
                        raise _idempotency_reused() from None
                    _assert_game_creation_matches(
                        concurrent_game,
                        request,
                        cipher,
                        daily_id=daily_id,
                        friend_id=friend_id,
                        room_id=room_id,
                    )
                return concurrent_game
        raise
    if commit:
        await session.commit()
    return game


async def submit_attempt(
    session: AsyncSession,
    principal: AuthPrincipal,
    game_id: str,
    guess: list[str],
    idempotency_key: str,
    request_id: str,
    cipher: SecretCipher,
    *,
    commit: bool = True,
    allow_duel: bool = False,
) -> GameSession:
    game = await load_owned_game(session, game_id, principal, for_update=True)
    previous = next(
        (attempt for attempt in game.attempts if attempt.idempotency_key == idempotency_key), None
    )
    if previous:
        if tuple(previous.guess) != tuple(item.upper() for item in guess):
            raise APIError(
                409,
                "IDEMPOTENCY_KEY_REUSED",
                "This idempotency key was already used for a different guess.",
            )
        return game
    if game.mode == GameMode.DUEL.value and not allow_duel:
        raise APIError(409, "REALTIME_ENDPOINT_REQUIRED", "Submit duel guesses in the live room.")
    if expire_game_record(game, now=utcnow()):
        await session.flush()
        if commit:
            await session.commit()
        raise APIError(410, "GAME_EXPIRED", "This game has expired.")
    if game.status != GameStatus.ACTIVE.value:
        raise APIError(409, "GAME_NOT_ACTIVE", "This game no longer accepts attempts.")
    config = GameConfig.from_dict(game.config)
    try:
        normalized_guess = validate_code(guess, config)
    except DomainError:
        game.invalid_submission_count += 1
        await session.commit()
        raise
    secret_code = cipher.decrypt(
        game.encrypted_secret,
        game.secret_nonce,
        game.secret_key_version,
        context=_cipher_context(game.public_id),
    )
    feedback = calculate_feedback(secret_code, normalized_guess)
    now = utcnow()
    if game.mode == GameMode.DAILY.value and game.attempts_used == 0:
        game.started_at = now
    game.attempts_used += 1
    attempt = GameAttempt(
        game_id=game.id,
        attempt_number=game.attempts_used,
        guess=list(normalized_guess),
        black_pegs=feedback.black,
        white_pegs=feedback.white,
        submitted_at=now,
        idempotency_key=idempotency_key,
        request_id=request_id,
    )
    game.attempts.append(attempt)
    if feedback.black == config.code_length:
        game.status = GameStatus.WON.value
    elif game.attempts_used >= game.maximum_attempts:
        game.status = GameStatus.LOST.value
    if GameStatus(game.status).terminal:
        game.completed_at = now
        game.elapsed_seconds = max(0, int((now - ensure_aware(game.started_at)).total_seconds()))
        breakdown = calculate_score(
            config,
            status=GameStatus(game.status),
            attempts_used=game.attempts_used,
            elapsed_seconds=game.elapsed_seconds,
        )
        game.final_score = breakdown.total
        game.score_breakdown = breakdown.to_dict()
        await _finalize_game(session, game, principal)
    await session.flush()
    if commit:
        await session.commit()
    return game


async def abandon(
    session: AsyncSession,
    principal: AuthPrincipal,
    game_id: str,
    cipher: SecretCipher,
    *,
    room_events: list[tuple[str, dict[str, object]]] | None = None,
) -> GameResponse:
    game = await load_owned_game(session, game_id, principal)
    if game.mode == GameMode.DUEL.value and game.room_id is not None:
        # Realtime submissions and finalizers lock room -> games. Preserve that
        # global order for HTTP abandonment so cross-player operations cannot
        # deadlock while each holds a different game row.
        await load_room_for_member(session, game.room_id, principal, for_update=True)
    game = await load_owned_game(session, game_id, principal, for_update=True)
    if expire_game_record(game, now=utcnow()):
        await session.commit()
        raise APIError(410, "GAME_EXPIRED", "This game has expired.")
    if game.status != GameStatus.ACTIVE.value:
        raise APIError(409, "GAME_NOT_ACTIVE", "This game is already complete.")
    game.status = GameStatus.ABANDONED.value
    game.completed_at = utcnow()
    game.elapsed_seconds = max(
        0, int((game.completed_at - ensure_aware(game.started_at)).total_seconds())
    )
    breakdown = calculate_score(
        GameConfig.from_dict(game.config),
        status=GameStatus.ABANDONED,
        attempts_used=game.attempts_used,
        elapsed_seconds=game.elapsed_seconds,
    )
    game.final_score = 0
    game.score_breakdown = breakdown.to_dict()
    game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
    if game.mode == GameMode.DUEL.value and game.room_id is not None:
        room = await session.scalar(
            select(MultiplayerRoom).where(MultiplayerRoom.id == game.room_id).with_for_update()
        )
        if room and room.status in {"waiting", "active"}:
            other_game = await session.scalar(
                select(GameSession).where(
                    GameSession.room_id == room.id,
                    GameSession.owner_id != principal.user_id,
                )
            )
            if room.status == "active" and other_game is not None:
                room.winner_id = other_game.owner_id
                room.winner_at = game.completed_at
                room.is_tie = False
                room.status = "completed"
                if other_game.status == GameStatus.ACTIVE.value:
                    other_game.status = GameStatus.ABANDONED.value
                    other_game.completed_at = game.completed_at
                    other_game.elapsed_seconds = max(
                        0,
                        int(
                            (
                                game.completed_at - ensure_aware(other_game.started_at)
                            ).total_seconds()
                        ),
                    )
                    other_game.final_score = 0
                    other_game.score_breakdown = calculate_score(
                        GameConfig.from_dict(other_game.config),
                        status=GameStatus.ABANDONED,
                        attempts_used=other_game.attempts_used,
                        elapsed_seconds=other_game.elapsed_seconds,
                    ).to_dict()
                    other_game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
                completion_event = await record_room_completion(session, room, "forfeit")
            else:
                room.status = "terminated"
                completion_event = await record_room_completion(session, room, "terminated")
            if completion_event is not None and room_events is not None:
                room_events.append((str(room.id), completion_event))
    await session.commit()
    return game_response(game, cipher)


async def _finalize_game(
    session: AsyncSession,
    game: GameSession,
    principal: AuthPrincipal,
) -> None:
    profile = await session.get(Profile, principal.user_id)
    settings = get_settings()
    if (
        await feature_enabled(session, settings, "leaderboards")
        and game.status == GameStatus.WON.value
        and game.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value
        and profile
        and not profile.is_anonymous
        and profile.public_leaderboards
    ):
        category = (
            f"daily:{game.daily_challenge_id}" if game.daily_challenge_id else game.difficulty
        )
        session.add(
            LeaderboardEntry(
                game_id=game.id,
                user_id=principal.user_id,
                category=category or "official",
                score=game.final_score or 0,
                attempts_used=game.attempts_used,
                elapsed_seconds=game.elapsed_seconds or 0,
                completed_at=game.completed_at or utcnow(),
            )
        )
    if (
        await feature_enabled(session, settings, "achievements")
        and profile is not None
        and not profile.is_anonymous
        and game.mode not in {GameMode.PRACTICE.value, GameMode.PASS_AND_PLAY.value}
    ):
        await _award_achievements(session, game, principal.user_id)


async def _award_achievements(
    session: AsyncSession,
    game: GameSession,
    user_id: uuid.UUID,
) -> None:
    keys: set[str] = set()
    if game.status == GameStatus.WON.value and game.attempts_used == game.maximum_attempts:
        keys.add("comeback")
    if (
        game.status == GameStatus.WON.value
        and game.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value
        and game.mode in {GameMode.SOLO.value, GameMode.DAILY.value}
    ):
        won_count = await session.scalar(
            select(func.count(GameSession.id)).where(
                GameSession.owner_id == user_id,
                GameSession.status == GameStatus.WON.value,
                GameSession.mode.in_([GameMode.SOLO.value, GameMode.DAILY.value]),
                GameSession.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value,
                GameSession.id != game.id,
            )
        )
        if not won_count:
            keys.add("first_break")
        if game.attempts_used == 1:
            keys.add("one_shot")
        if game.invalid_submission_count == 0:
            keys.add("no_waste")
        if game.difficulty == "hard":
            keys.add("hard_mode")
        if game.difficulty == "expert":
            keys.add("expert_breaker")
    if game.mode == GameMode.DAILY.value and GameStatus(game.status).terminal:
        keys.add("daily_debut")
        prior_daily_completions = await session.scalar(
            select(func.count(func.distinct(GameSession.daily_challenge_id))).where(
                GameSession.owner_id == user_id,
                GameSession.mode == GameMode.DAILY.value,
                GameSession.completed_at.is_not(None),
                GameSession.id != game.id,
            )
        )
        if (prior_daily_completions or 0) + 1 >= 7:
            keys.add("logic_week")
    if game.mode == GameMode.FRIEND_CHALLENGE.value and GameStatus(game.status).terminal:
        keys.add("challenger")
    for key in keys:
        try:
            async with session.begin_nested():
                session.add(UserAchievement(user_id=user_id, achievement_key=key, game_id=game.id))
                await session.flush()
        except IntegrityError:
            pass


async def get_or_create_daily(
    session: AsyncSession,
    settings: Settings,
    cipher: SecretCipher,
    challenge_date: date | None = None,
) -> DailyChallenge:
    day = challenge_date or utcnow().date()
    existing = await session.scalar(
        select(DailyChallenge).where(
            DailyChallenge.challenge_date == day,
            DailyChallenge.rule_set_version == RULE_SET_VERSION,
        )
    )
    if existing:
        return existing
    try:
        daily_keys = settings.daily_hmac_keyring()
        active_key_version = settings.daily_hmac_active_key_version
        daily_keys[active_key_version]
    except (KeyError, ValueError):
        raise APIError(
            503, "DAILY_UNAVAILABLE", "The daily challenge is temporarily unavailable."
        ) from None
    config = get_preset("normal")
    public_id = daily_challenge_id(day)
    daily = DailyChallenge(
        challenge_date=day,
        public_id=public_id,
        config=config.to_dict(),
        derivation_version=DAILY_DERIVATION_VERSION,
        derivation_key_version=active_key_version,
        rule_set_version=RULE_SET_VERSION,
    )
    session.add(daily)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        concurrent = await session.scalar(
            select(DailyChallenge).where(
                DailyChallenge.challenge_date == day,
                DailyChallenge.rule_set_version == RULE_SET_VERSION,
            )
        )
        if concurrent:
            return concurrent
        raise
    return daily


async def start_daily(
    session: AsyncSession,
    principal: AuthPrincipal,
    settings: Settings,
    cipher: SecretCipher,
    *,
    practice: bool = False,
) -> GameSession:
    await ensure_profile(session, principal)
    daily = await get_or_create_daily(session, settings, cipher)
    existing = await session.scalar(
        select(GameSession)
        .options(selectinload(GameSession.attempts))
        .where(
            GameSession.owner_id == principal.user_id,
            GameSession.daily_challenge_id == daily.id,
        )
    )
    if existing is not None and expire_game_record(existing, now=utcnow()):
        await session.commit()
    if existing and (existing.status == GameStatus.ACTIVE.value or not practice):
        return existing
    try:
        derivation_key = settings.daily_hmac_keyring()[daily.derivation_key_version]
    except (KeyError, ValueError):
        raise APIError(
            503, "DAILY_UNAVAILABLE", "The daily challenge is temporarily unavailable."
        ) from None
    secret_code = derive_daily_secret(
        daily.challenge_date,
        GameConfig.from_dict(daily.config),
        derivation_key,
    )
    request = CreateGameRequest(
        mode=GameMode.PRACTICE if practice else GameMode.DAILY,
        difficulty="normal",
    )
    return await create_game(
        session,
        principal,
        request,
        cipher,
        secret_override=secret_code,
        daily_id=None if practice else daily.id,
    )


async def create_challenge(
    session: AsyncSession,
    principal: AuthPrincipal,
    request: CreateChallengeRequest,
    cipher: SecretCipher,
    settings: Settings,
) -> tuple[FriendChallenge, str]:
    await ensure_profile(session, principal)
    await session.scalar(select(Profile).where(Profile.id == principal.user_id).with_for_update())
    fingerprint = (
        creation_request_fingerprint(
            "challenge.create",
            request.model_dump(mode="json", by_alias=True, exclude={"idempotency_key"}),
            settings,
        )
        if request.idempotency_key
        else None
    )

    def expected_payload() -> tuple[GameConfig, tuple[str, ...] | None]:
        expected_config, _ = resolve_config(request.difficulty, request.config)
        expected_config = GameConfig.from_dict(
            expected_config.to_dict()
            | {
                "ranked": False,
                "visibility": "shareable",
                "codeMaker": "human" if request.secret else "computer",
            }
        )
        expected_secret = validate_code(request.secret, expected_config) if request.secret else None
        return expected_config, expected_secret

    def assert_same_payload(existing: FriendChallenge) -> None:
        expected_config, expected_secret = expected_payload()
        if (
            existing.title != request.title
            or existing.show_creator_name != request.show_creator_name
            or existing.config != expected_config.to_dict()
        ):
            raise _idempotency_reused()
        if expected_secret is not None:
            stored_secret = cipher.decrypt(
                existing.encrypted_secret,
                existing.secret_nonce,
                existing.secret_key_version,
                context=f"challenge:{existing.share_code_hash}:{RULE_SET_VERSION}",
            )
            if stored_secret != expected_secret:
                raise _idempotency_reused()

    if request.idempotency_key:
        share_code = idempotent_invite_code(
            "friend", principal.user_id, request.idempotency_key, settings
        )
        existing = await session.scalar(
            select(FriendChallenge).where(
                FriendChallenge.creator_id == principal.user_id,
                FriendChallenge.creation_idempotency_key == request.idempotency_key,
            )
        )
        if existing:
            if (
                existing.creation_request_fingerprint is not None
                and existing.creation_request_fingerprint != fingerprint
            ):
                raise _idempotency_reused()
            assert_same_payload(existing)
            return existing, share_code
    active_challenges = await session.scalar(
        select(func.count(FriendChallenge.id)).where(
            FriendChallenge.creator_id == principal.user_id,
            FriendChallenge.revoked_at.is_(None),
            FriendChallenge.expires_at > utcnow(),
        )
    )
    challenge_limit = (
        MAX_ACTIVE_GUEST_CHALLENGES if principal.is_anonymous else MAX_ACTIVE_CHALLENGES_PER_USER
    )
    if (active_challenges or 0) >= challenge_limit:
        raise APIError(
            409,
            "CHALLENGE_LIMIT_REACHED",
            "Revoke an active challenge before creating another one.",
        )
    config, requested_secret = expected_payload()
    secret_code = requested_secret or generate_secret(config)
    share_code = (
        idempotent_invite_code("friend", principal.user_id, request.idempotency_key, settings)
        if request.idempotency_key
        else public_token(18)
    )
    share_code_hash = identifier_hash(share_code, settings)
    context = f"challenge:{share_code_hash}:{RULE_SET_VERSION}"
    encrypted = cipher.encrypt(secret_code, context=context)
    challenge = FriendChallenge(
        share_code_hash=share_code_hash,
        creation_idempotency_key=request.idempotency_key,
        creation_request_fingerprint=fingerprint,
        creator_id=principal.user_id,
        title=request.title,
        show_creator_name=request.show_creator_name,
        config=config.to_dict(),
        encrypted_secret=encrypted.ciphertext,
        secret_nonce=encrypted.nonce,
        secret_key_version=encrypted.key_version,
        expires_at=utcnow() + timedelta(days=30),
    )
    session.add(challenge)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if request.idempotency_key:
            concurrent = await session.scalar(
                select(FriendChallenge).where(
                    FriendChallenge.creator_id == principal.user_id,
                    FriendChallenge.creation_idempotency_key == request.idempotency_key,
                )
            )
            if concurrent:
                if (
                    concurrent.creation_request_fingerprint is not None
                    and concurrent.creation_request_fingerprint != fingerprint
                ):
                    raise _idempotency_reused() from None
                assert_same_payload(concurrent)
                return concurrent, share_code
        raise
    return challenge, share_code


async def challenge_response(
    session: AsyncSession,
    challenge: FriendChallenge,
    principal: AuthPrincipal | None = None,
    public_code: str | None = None,
) -> ChallengeResponse:
    creator = await session.get(Profile, challenge.creator_id)
    count = await session.scalar(
        select(func.count(GameSession.id)).where(
            GameSession.friend_challenge_id == challenge.id,
            GameSession.completed_at.is_not(None),
        )
    )
    is_owner = principal is not None and principal.user_id == challenge.creator_id
    return ChallengeResponse(
        id=str(challenge.id) if is_owner else None,
        share_code=public_code or "",
        title=challenge.title,
        creator_name=(
            (creator.display_name or "Anonymous breaker")
            if challenge.show_creator_name and creator and creator.deleted_at is None
            else None
        ),
        config=GameConfigSchema.model_validate(challenge.config),
        expires_at=challenge.expires_at,
        revoked=challenge.revoked_at is not None,
        completed_count=count or 0 if is_owner else 0,
    )


async def load_challenge(
    session: AsyncSession, share_code: str, settings: Settings
) -> FriendChallenge:
    challenge = await session.scalar(
        select(FriendChallenge).where(
            FriendChallenge.share_code_hash == identifier_hash(share_code, settings)
        )
    )
    if challenge is None:
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    if challenge.revoked_at or ensure_aware(challenge.expires_at) <= utcnow():
        # Capability-token lookups deliberately do not distinguish absent,
        # expired, and revoked records.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    return challenge


async def start_challenge(
    session: AsyncSession,
    principal: AuthPrincipal,
    challenge: FriendChallenge,
    cipher: SecretCipher,
    *,
    practice: bool = False,
) -> GameSession:
    await ensure_profile(session, principal)
    existing = await session.scalar(
        select(GameSession)
        .options(selectinload(GameSession.attempts))
        .where(
            GameSession.owner_id == principal.user_id,
            GameSession.friend_challenge_id == challenge.id,
        )
    )
    if existing is not None and expire_game_record(existing, now=utcnow()):
        await session.commit()
    if existing and (existing.status == GameStatus.ACTIVE.value or not practice):
        return existing
    config = GameConfig.from_dict(challenge.config)
    secret_code = cipher.decrypt(
        challenge.encrypted_secret,
        challenge.secret_nonce,
        challenge.secret_key_version,
        context=f"challenge:{challenge.share_code_hash}:{RULE_SET_VERSION}",
    )
    request = CreateGameRequest(
        mode=GameMode.PRACTICE if practice else GameMode.FRIEND_CHALLENGE,
        config=GameConfigSchema.model_validate(config.to_dict()),
    )
    return await create_game(
        session,
        principal,
        request,
        cipher,
        secret_override=secret_code,
        friend_id=None if practice else challenge.id,
        linked_expires_at=None if practice else challenge.expires_at,
    )


async def create_room(
    session: AsyncSession,
    principal: AuthPrincipal,
    difficulty: str,
    cipher: SecretCipher,
    settings: Settings,
    idempotency_key: str | None = None,
) -> tuple[MultiplayerRoom, str]:
    await ensure_profile(session, principal)
    fingerprint = (
        creation_request_fingerprint("room.create", {"difficulty": difficulty}, settings)
        if idempotency_key
        else None
    )
    if idempotency_key:
        room_code = idempotent_invite_code("room", principal.user_id, idempotency_key, settings)
        existing = await session.scalar(
            select(MultiplayerRoom).where(
                MultiplayerRoom.owner_id == principal.user_id,
                MultiplayerRoom.creation_idempotency_key == idempotency_key,
            )
        )
        if existing:
            if (
                existing.creation_request_fingerprint is not None
                and existing.creation_request_fingerprint != fingerprint
            ):
                raise _idempotency_reused()
            if existing.config != get_preset(difficulty).to_dict():
                raise _idempotency_reused()
            return existing, room_code
    config = get_preset(difficulty)
    secret_code = generate_secret(config)
    room_code = (
        idempotent_invite_code("room", principal.user_id, idempotency_key, settings)
        if idempotency_key
        else public_token(16)
    )
    room_id = uuid.uuid4()
    context = f"room:{room_id}:{RULE_SET_VERSION}"
    encrypted = cipher.encrypt(secret_code, context=context)
    room = MultiplayerRoom(
        id=room_id,
        room_code_hash=identifier_hash(room_code, settings),
        creation_idempotency_key=idempotency_key,
        creation_request_fingerprint=fingerprint,
        owner_id=principal.user_id,
        config=config.to_dict(),
        encrypted_secret=encrypted.ciphertext,
        secret_nonce=encrypted.nonce,
        secret_key_version=encrypted.key_version,
        expires_at=utcnow() + timedelta(hours=2),
    )
    session.add(room)
    try:
        # The models intentionally use identifiers instead of a write-side ORM
        # relationship. Flush the parent explicitly so PostgreSQL cannot order the
        # member insert ahead of its room foreign key.
        await session.flush()
        session.add(MultiplayerMember(room_id=room.id, user_id=principal.user_id))
        await session.flush()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if idempotency_key:
            concurrent = await session.scalar(
                select(MultiplayerRoom).where(
                    MultiplayerRoom.owner_id == principal.user_id,
                    MultiplayerRoom.creation_idempotency_key == idempotency_key,
                )
            )
            if concurrent:
                if (
                    concurrent.creation_request_fingerprint is not None
                    and concurrent.creation_request_fingerprint != fingerprint
                ):
                    raise _idempotency_reused() from None
                if concurrent.config != config.to_dict():
                    raise _idempotency_reused() from None
                return concurrent, room_code
        raise
    return room, room_code


async def _create_room_game(
    session: AsyncSession,
    principal: AuthPrincipal,
    room: MultiplayerRoom,
    config: GameConfig,
    secret_code: tuple[str, ...],
    cipher: SecretCipher,
) -> GameSession:
    request = CreateGameRequest(
        mode=GameMode.DUEL,
        difficulty=preset_name(config) or "normal",
    )
    return await create_game(
        session,
        principal,
        request,
        cipher,
        secret_override=secret_code,
        room_id=room.id,
        linked_expires_at=room.expires_at,
        commit=False,
    )


async def join_room(
    session: AsyncSession,
    principal: AuthPrincipal,
    room_code: str,
    _cipher: SecretCipher,
    settings: Settings,
) -> MultiplayerRoom:
    await ensure_profile(session, principal)
    room = await session.scalar(
        select(MultiplayerRoom)
        .where(MultiplayerRoom.room_code_hash == identifier_hash(room_code, settings))
        .with_for_update()
    )
    if room is None:
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found.")
    if ensure_aware(room.expires_at) <= utcnow():
        raise APIError(410, "ROOM_EXPIRED", "This room has expired.")
    member = await session.scalar(
        select(MultiplayerMember).where(
            MultiplayerMember.room_id == room.id,
            MultiplayerMember.user_id == principal.user_id,
        )
    )
    members_count = await session.scalar(
        select(func.count(MultiplayerMember.id)).where(MultiplayerMember.room_id == room.id)
    )
    if member is None:
        if (members_count or 0) >= 2:
            raise APIError(409, "ROOM_FULL", "This room already has two players.")
        if room.status != "waiting":
            raise APIError(409, "ROOM_NOT_JOINABLE", "This room is no longer accepting players.")
        session.add(MultiplayerMember(room_id=room.id, user_id=principal.user_id))
    await session.commit()
    return room


async def ready_room(
    session: AsyncSession,
    principal: AuthPrincipal,
    room_id: uuid.UUID,
    cipher: SecretCipher,
) -> tuple[MultiplayerRoom, list[dict[str, object]]]:
    """Mark a room member ready and atomically start a full two-player room."""

    room = await load_room_for_member(session, room_id, principal, for_update=True)
    if room.status == "expired":
        await session.commit()
        raise APIError(410, "ROOM_EXPIRED", "This room has expired.")
    member = await session.scalar(
        select(MultiplayerMember)
        .where(
            MultiplayerMember.room_id == room.id,
            MultiplayerMember.user_id == principal.user_id,
        )
        .with_for_update()
    )
    if member is None:
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found or you are not a member.")
    if room.status != "waiting":
        if member.ready:
            await session.commit()
            return room, []
        raise APIError(409, "ROOM_ALREADY_STARTED", "This room has already started.")

    events: list[dict[str, object]] = []
    if not member.ready:
        member.ready = True
        member.ready_at = utcnow()
        events.append(
            await record_room_event(
                session,
                room,
                "member_ready",
                {
                    "userId": str(principal.user_id),
                    "ready": True,
                    "readyAt": member.ready_at.isoformat(),
                },
            )
        )

    member_rows = (
        await session.execute(
            select(MultiplayerMember, Profile)
            .join(Profile, Profile.id == MultiplayerMember.user_id)
            .where(MultiplayerMember.room_id == room.id)
            .order_by(MultiplayerMember.joined_at, MultiplayerMember.id)
        )
    ).all()
    if len(member_rows) == 2 and all(room_member.ready for room_member, _ in member_rows):
        config = GameConfig.from_dict(room.config)
        secret_code = cipher.decrypt(
            room.encrypted_secret,
            room.secret_nonce,
            room.secret_key_version,
            context=f"room:{room.id}:{RULE_SET_VERSION}",
        )
        existing_owner_ids = set(
            await session.scalars(
                select(GameSession.owner_id).where(GameSession.room_id == room.id)
            )
        )
        duel_started_at = utcnow()
        for room_member, profile in member_rows:
            if room_member.user_id in existing_owner_ids:
                continue
            room_principal = AuthPrincipal(
                user_id=room_member.user_id,
                is_anonymous=profile.is_anonymous,
                session_id=None,
                issued_at=duel_started_at,
                authenticated_at=None,
                assurance_level=None,
            )
            game = await _create_room_game(
                session, room_principal, room, config, secret_code, cipher
            )
            game.started_at = duel_started_at
        await session.execute(
            update(GameSession)
            .where(GameSession.room_id == room.id)
            .values(started_at=duel_started_at)
        )
        room.status = "active"
        events.append(
            await record_room_event(
                session,
                room,
                "room_started",
                {"startedAt": duel_started_at.isoformat()},
            )
        )
    await session.commit()
    return room, events


async def load_room_for_member(
    session: AsyncSession,
    room_id: uuid.UUID,
    principal: AuthPrincipal,
    *,
    for_update: bool = False,
) -> MultiplayerRoom:
    await ensure_profile(session, principal)
    query = (
        select(MultiplayerRoom)
        .join(MultiplayerMember, MultiplayerMember.room_id == MultiplayerRoom.id)
        .where(MultiplayerRoom.id == room_id, MultiplayerMember.user_id == principal.user_id)
    )
    if for_update:
        query = query.with_for_update()
    room = await session.scalar(query)
    if room is None:
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found or you are not a member.")
    if ensure_aware(room.expires_at) <= utcnow():
        room.status = "expired"
    games_query = select(GameSession).where(GameSession.room_id == room.id).order_by(GameSession.id)
    if for_update:
        games_query = games_query.with_for_update()
    games = (await session.scalars(games_query)).all()
    if (
        for_update
        and room.status == "active"
        and len(games) == 2
        and all(GameStatus(game.status).terminal for game in games)
    ):
        won_games = sorted(
            (game for game in games if game.status == GameStatus.WON.value),
            key=lambda game: ensure_aware(game.completed_at or utcnow()),
        )
        room.status = "completed"
        if not won_games:
            room.winner_id = None
            room.winner_at = None
            room.is_tie = True
        elif len(won_games) == 2:
            first_at = ensure_aware(won_games[0].completed_at or utcnow())
            second_at = ensure_aware(won_games[1].completed_at or utcnow())
            room.is_tie = (second_at - first_at).total_seconds() * 1000 <= (
                get_settings().room_tie_window_ms
            )
            if room.is_tie:
                room.winner_id = None
                room.winner_at = first_at
            else:
                room.winner_id = won_games[0].owner_id
                room.winner_at = first_at
        else:
            room.winner_id = won_games[0].owner_id
            room.winner_at = won_games[0].completed_at
            room.is_tie = False
    return room


async def room_response(
    session: AsyncSession,
    room: MultiplayerRoom,
    room_code: str | None = None,
    viewer_id: uuid.UUID | None = None,
) -> RoomResponse:
    rows = (
        await session.execute(
            select(MultiplayerMember, Profile, GameSession)
            .join(Profile, Profile.id == MultiplayerMember.user_id)
            .outerjoin(
                GameSession,
                and_(
                    GameSession.room_id == MultiplayerMember.room_id,
                    GameSession.owner_id == MultiplayerMember.user_id,
                ),
            )
            .where(MultiplayerMember.room_id == room.id)
            .order_by(MultiplayerMember.joined_at)
        )
    ).all()
    members = [
        RoomMemberResponse(
            user_id=member.user_id,
            display_name=profile.display_name or "Anonymous breaker",
            connected=member.connected,
            ready=member.ready,
            ready_at=member.ready_at,
            attempts_used=game.attempts_used if game else 0,
            completed=bool(game and GameStatus(game.status).terminal),
            game_id=(game.public_id if game is not None and member.user_id == viewer_id else None),
        )
        for member, profile, game in rows
    ]
    return RoomResponse(
        id=room.id,
        room_code=room_code,
        status=room.status,
        config=GameConfigSchema.model_validate(room.config),
        members=members,
        winner_id=room.winner_id,
        is_tie=room.is_tie,
        expires_at=room.expires_at,
        event_sequence=room.event_sequence,
    )


async def profile_response(session: AsyncSession, principal: AuthPrincipal) -> ProfileResponse:
    profile = await ensure_profile(session, principal)
    await session.commit()
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        is_anonymous=profile.is_anonymous,
        public_leaderboards=profile.public_leaderboards,
        created_at=profile.created_at,
    )


def normalize_display_name(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def csv_safe(value: object) -> str:
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


async def export_user_csv(session: AsyncSession, principal: AuthPrincipal) -> str:
    profile = await session.get(Profile, principal.user_id)
    player_name = profile.display_name if profile and profile.display_name else "Anonymous breaker"
    games = (
        await session.scalars(
            select(GameSession)
            .where(GameSession.owner_id == principal.user_id)
            .order_by(GameSession.created_at)
        )
    ).all()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "timestamp",
            "player_name",
            "mode",
            "difficulty",
            "code_maker",
            "number_of_colours",
            "code_length",
            "duplicates_allowed",
            "attempts_used",
            "maximum_attempts",
            "score",
            "scoring_version",
            "result",
        ]
    )
    for game in games:
        config = GameConfig.from_dict(game.config)
        writer.writerow(
            [
                ensure_aware(game.created_at).isoformat(),
                csv_safe(player_name),
                csv_safe(game.mode),
                csv_safe(game.difficulty or "custom"),
                config.code_maker.value,
                len(config.colours),
                config.code_length,
                str(config.duplicates_allowed).lower(),
                game.attempts_used,
                game.maximum_attempts,
                game.final_score or 0,
                game.scoring_version,
                game.status,
            ]
        )
    return output.getvalue()


def _csv_document(header: list[str], rows: list[list[object]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerows([[csv_safe(value) for value in row] for row in rows])
    return output.getvalue()


async def export_user_archive(session: AsyncSession, principal: AuthPrincipal) -> bytes:
    """Build a complete, secret-free, portable account export."""
    profile = await session.get(Profile, principal.user_id)
    if profile is None:
        raise APIError(404, "PROFILE_NOT_FOUND", "Profile not found.")
    games = (
        await session.scalars(
            select(GameSession)
            .options(selectinload(GameSession.attempts))
            .where(GameSession.owner_id == principal.user_id)
            .order_by(GameSession.created_at)
        )
    ).all()
    achievements = (
        await session.execute(
            select(
                UserAchievement.achievement_key,
                UserAchievement.awarded_at,
                UserAchievement.game_id,
            )
            .where(UserAchievement.user_id == principal.user_id)
            .order_by(UserAchievement.awarded_at)
        )
    ).all()
    challenges = (
        await session.scalars(
            select(FriendChallenge)
            .where(FriendChallenge.creator_id == principal.user_id)
            .order_by(FriendChallenge.created_at)
        )
    ).all()
    memberships = (
        await session.execute(
            select(MultiplayerMember, MultiplayerRoom)
            .join(MultiplayerRoom, MultiplayerRoom.id == MultiplayerMember.room_id)
            .where(MultiplayerMember.user_id == principal.user_id)
            .order_by(MultiplayerMember.joined_at)
        )
    ).all()

    profile_document = {
        "id": str(profile.id),
        "displayName": profile.display_name,
        "isAnonymous": profile.is_anonymous,
        "publicLeaderboards": profile.public_leaderboards,
        "createdAt": ensure_aware(profile.created_at).isoformat(),
        "exportedAt": utcnow().isoformat(),
    }
    game_rows: list[list[object]] = []
    attempt_rows: list[list[object]] = []
    for game in games:
        game_rows.append(
            [
                game.public_id,
                ensure_aware(game.created_at).isoformat(),
                game.mode,
                game.difficulty or "custom",
                json.dumps(game.config, ensure_ascii=False, sort_keys=True),
                game.status,
                game.attempts_used,
                game.maximum_attempts,
                game.final_score or 0,
                game.scoring_version,
                game.ranked_eligibility,
                ensure_aware(game.completed_at).isoformat() if game.completed_at else "",
            ]
        )
        attempt_rows.extend(
            [
                game.public_id,
                attempt.attempt_number,
                json.dumps(attempt.guess, ensure_ascii=False),
                attempt.black_pegs,
                attempt.white_pegs,
                ensure_aware(attempt.submitted_at).isoformat(),
            ]
            for attempt in game.attempts
        )

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr(
            "manifest.json",
            json.dumps(
                {
                    "formatVersion": 1,
                    "files": [
                        "profile.json",
                        "games.csv",
                        "attempts.csv",
                        "achievements.csv",
                        "challenges.csv",
                        "rooms.csv",
                    ],
                    "excluded": [
                        "authentication credentials",
                        "active and historical secret codes",
                        "invite tokens",
                        "encryption material",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        output.writestr("profile.json", json.dumps(profile_document, ensure_ascii=False, indent=2))
        output.writestr(
            "games.csv",
            _csv_document(
                [
                    "game_id",
                    "created_at",
                    "mode",
                    "difficulty",
                    "config",
                    "result",
                    "attempts_used",
                    "maximum_attempts",
                    "score",
                    "scoring_version",
                    "ranking_eligibility",
                    "completed_at",
                ],
                game_rows,
            ),
        )
        output.writestr(
            "attempts.csv",
            _csv_document(
                [
                    "game_id",
                    "attempt_number",
                    "guess",
                    "black_pegs",
                    "white_pegs",
                    "submitted_at",
                ],
                attempt_rows,
            ),
        )
        output.writestr(
            "achievements.csv",
            _csv_document(
                ["achievement_key", "awarded_at", "game_id"],
                [
                    [key, ensure_aware(awarded_at).isoformat(), game_id or ""]
                    for key, awarded_at, game_id in achievements
                ],
            ),
        )
        output.writestr(
            "challenges.csv",
            _csv_document(
                [
                    "challenge_id",
                    "title",
                    "show_creator_name",
                    "config",
                    "created_at",
                    "expires_at",
                    "revoked_at",
                ],
                [
                    [
                        challenge.id,
                        challenge.title or "",
                        challenge.show_creator_name,
                        json.dumps(challenge.config, ensure_ascii=False, sort_keys=True),
                        ensure_aware(challenge.created_at).isoformat(),
                        ensure_aware(challenge.expires_at).isoformat(),
                        (
                            ensure_aware(challenge.revoked_at).isoformat()
                            if challenge.revoked_at
                            else ""
                        ),
                    ]
                    for challenge in challenges
                ],
            ),
        )
        output.writestr(
            "rooms.csv",
            _csv_document(
                ["room_id", "status", "joined_at", "expires_at", "is_tie", "won"],
                [
                    [
                        room.id,
                        room.status,
                        ensure_aware(member.joined_at).isoformat(),
                        ensure_aware(room.expires_at).isoformat(),
                        room.is_tie,
                        room.winner_id == principal.user_id,
                    ]
                    for member, room in memberships
                ],
            ),
        )
    return archive.getvalue()


async def delete_account(session: AsyncSession, principal: AuthPrincipal) -> None:
    profile = await session.get(Profile, principal.user_id)
    if profile is None:
        profile = await ensure_profile(session, principal)
    if profile.deleted_at is not None:
        return
    profile.display_name = None
    profile.normalized_display_name = None
    profile.is_anonymous = True
    profile.public_leaderboards = False
    profile.deleted_at = utcnow()
    await session.execute(
        update(LeaderboardEntry)
        .where(LeaderboardEntry.user_id == principal.user_id)
        .values(invalidated_at=utcnow(), review_status="deleted_account")
    )
    await session.execute(
        update(FriendChallenge)
        .where(FriendChallenge.creator_id == principal.user_id)
        .values(
            revoked_at=func.coalesce(FriendChallenge.revoked_at, utcnow()),
            title=None,
            show_creator_name=False,
        )
    )
    await session.execute(
        update(MultiplayerRoom)
        .where(
            MultiplayerRoom.owner_id == principal.user_id,
            MultiplayerRoom.status.in_(["waiting", "active"]),
        )
        .values(status="terminated")
    )
    await session.execute(
        delete(UserAchievement).where(UserAchievement.user_id == principal.user_id)
    )
    await session.execute(delete(SupportRequest).where(SupportRequest.user_id == principal.user_id))
    await session.execute(delete(AdminGrant).where(AdminGrant.user_id == principal.user_id))
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            action="account.deleted",
            target_type="profile",
            target_id=str(principal.user_id),
            event_data={},
        )
    )
    await session.commit()
