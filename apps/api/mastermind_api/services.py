# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `base64` so the module can use that dependency.
import base64

# Imports `csv` so the module can use that dependency.
import csv

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports `hmac` so the module can use that dependency.
import hmac

# Imports `io` so the module can use that dependency.
import io

# Imports `json` so the module can use that dependency.
import json

# Imports `secrets` so the module can use that dependency.
import secrets

# Imports `unicodedata` so the module can use that dependency.
import unicodedata

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports `zipfile` so the module can use that dependency.
import zipfile

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, date, datetime, timedelta

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import (
    # Supplies this item to the surrounding call or collection.
    DAILY_DERIVATION_VERSION,
    # Supplies this item to the surrounding call or collection.
    RULE_SET_VERSION,
    # Supplies this item to the surrounding call or collection.
    SCORING_VERSION,
    # Supplies this item to the surrounding call or collection.
    CodeMakerType,
    # Supplies this item to the surrounding call or collection.
    DomainError,
    # Supplies this item to the surrounding call or collection.
    GameConfig,
    # Supplies this item to the surrounding call or collection.
    GameMode,
    # Supplies this item to the surrounding call or collection.
    GameStatus,
    # Supplies this item to the surrounding call or collection.
    LeaderboardEligibility,
    # Supplies this item to the surrounding call or collection.
    calculate_feedback,
    # Supplies this item to the surrounding call or collection.
    calculate_score,
    # Supplies this item to the surrounding call or collection.
    daily_challenge_id,
    # Supplies this item to the surrounding call or collection.
    derive_daily_secret,
    # Supplies this item to the surrounding call or collection.
    generate_secret,
    # Supplies this item to the surrounding call or collection.
    get_preset,
    # Supplies this item to the surrounding call or collection.
    preset_name,
    # Supplies this item to the surrounding call or collection.
    validate_code,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports the required names from `pymongo.errors` for this module.
from pymongo.errors import DuplicateKeyError

# Imports selected names from `.auth` for use in this module.
from .auth import AuthPrincipal

# Imports selected names from `.config` for use in this module.
from .config import Settings, get_settings

# Imports selected names from `.crypto` for use in this module.
from .crypto import SecretCipher

# Imports the required names from `.database` for this module.
from .database import MongoSession

# Imports selected names from `.errors` for use in this module.
from .errors import APIError

# Imports selected names from `.features` for use in this module.
from .features import feature_enabled

# Imports selected names from `.models` for use in this module.
from .models import (
    # Supplies this item to the surrounding call or collection.
    AdminGrant,
    # Supplies this item to the surrounding call or collection.
    AuditEvent,
    # Supplies this item to the surrounding call or collection.
    DailyChallenge,
    # Supplies this item to the surrounding call or collection.
    FriendChallenge,
    # Supplies this item to the surrounding call or collection.
    GameAttempt,
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    LeaderboardEntry,
    # Supplies this item to the surrounding call or collection.
    MultiplayerMember,
    # Supplies this item to the surrounding call or collection.
    MultiplayerRoom,
    # Supplies this item to the surrounding call or collection.
    Profile,
    # Supplies this item to the surrounding call or collection.
    SupportRequest,
    # Supplies this item to the surrounding call or collection.
    UserAchievement,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `.realtime` for use in this module.
from .realtime import (
    # Supplies this item to the surrounding call or collection.
    record_room_completion,
    # Supplies this item to the surrounding call or collection.
    record_room_event,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `.retention` for use in this module.
from .retention import expire_game_record, game_expiry_for_mode

# Imports selected names from `.schemas` for use in this module.
from .schemas import (
    # Supplies this item to the surrounding call or collection.
    AttemptSchema,
    # Supplies this item to the surrounding call or collection.
    ChallengeResponse,
    # Supplies this item to the surrounding call or collection.
    CreateChallengeRequest,
    # Supplies this item to the surrounding call or collection.
    CreateGameRequest,
    # Supplies this item to the surrounding call or collection.
    FeedbackSchema,
    # Supplies this item to the surrounding call or collection.
    GameConfigSchema,
    # Supplies this item to the surrounding call or collection.
    GameResponse,
    # Supplies this item to the surrounding call or collection.
    ProfileResponse,
    # Supplies this item to the surrounding call or collection.
    RoomMemberResponse,
    # Supplies this item to the surrounding call or collection.
    RoomResponse,
    # Supplies this item to the surrounding call or collection.
    ScoreBreakdownSchema,
    # Closes the multiline call, declaration, or collection started above.
)

# Computes and stores `OFFICIAL_GAME_MODES` for subsequent operations.
OFFICIAL_GAME_MODES = {GameMode.SOLO, GameMode.DAILY}
# Computes and stores `MAX_ACTIVE_CHALLENGES_PER_USER` for subsequent operations.
MAX_ACTIVE_CHALLENGES_PER_USER = 25
# Computes and stores `MAX_ACTIVE_GUEST_CHALLENGES` for subsequent operations.
MAX_ACTIVE_GUEST_CHALLENGES = 3


# Defines the `utcnow` callable and its typed interface.
def utcnow() -> datetime:
    # Returns this result to the caller and ends the current function.
    return datetime.now(UTC)


# Defines the `ensure_aware` callable and its typed interface.
def ensure_aware(value: datetime) -> datetime:
    # Returns this result to the caller and ends the current function.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# Defines the `public_token` callable and its typed interface.
def public_token(bytes_count: int = 16) -> str:
    # Returns this result to the caller and ends the current function.
    return secrets.token_urlsafe(bytes_count).rstrip("=")


# Defines the `identifier_hash` callable and its typed interface.
def identifier_hash(value: str, settings: Settings) -> str:
    # Computes and stores `key` for subsequent operations.
    key = settings.public_identifier_hmac_key.encode()
    # Checks this condition before executing the nested branch.
    if len(key) < 32:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "INVITES_UNAVAILABLE", "Private invites are temporarily unavailable.")
    # Returns this result to the caller and ends the current function.
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


# Defines the `idempotent_invite_code` callable and its typed interface.
def idempotent_invite_code(
    # Declares the typed `namespace` data field.
    namespace: str,
    # Declares the typed `user_id` data field.
    user_id: uuid.UUID,
    # Declares the typed `idempotency_key` data field.
    idempotency_key: str,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> str:
    # Computes and stores `key` for subsequent operations.
    key = settings.public_identifier_hmac_key.encode()
    # Checks this condition before executing the nested branch.
    if len(key) < 32:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "INVITES_UNAVAILABLE", "Private invites are temporarily unavailable.")
    # Computes and stores `digest` for subsequent operations.
    digest = hmac.new(
        # Supplies this item to the surrounding call or collection.
        key,
        # Supplies this item to the surrounding call or collection.
        f"{namespace}|{user_id}|{idempotency_key}".encode(),
        # Supplies this item to the surrounding call or collection.
        hashlib.sha256,
        # Executes this statement as the next step in the surrounding logic.
    ).digest()
    # Returns this result to the caller and ends the current function.
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


# Defines the `creation_request_fingerprint` callable and its typed interface.
def creation_request_fingerprint(
    # Declares the typed `operation` data field.
    operation: str,
    # Declares the typed `payload` data field.
    payload: dict[str, object],
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> str:
    # Computes and stores `key` for subsequent operations.
    key = settings.public_identifier_hmac_key.encode()
    # Checks this condition before executing the nested branch.
    if len(key) < 32:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(503, "IDEMPOTENCY_UNAVAILABLE", "Safe request retries are unavailable.")
    # Computes and stores `canonical` for subsequent operations.
    canonical = json.dumps(
        # Supplies this item to the surrounding call or collection.
        {"operation": operation, "payload": payload},
        # Provides the `ensure_ascii` parameter or keyword argument.
        ensure_ascii=True,
        # Provides the `sort_keys` parameter or keyword argument.
        sort_keys=True,
        # Provides the `separators` parameter or keyword argument.
        separators=(",", ":"),
        # Executes this statement as the next step in the surrounding logic.
    ).encode()
    # Returns this result to the caller and ends the current function.
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


# Defines the `config_from_schema` callable and its typed interface.
def config_from_schema(schema: GameConfigSchema) -> GameConfig:
    # Returns this result to the caller and ends the current function.
    return GameConfig(
        # Provides the `colours` parameter or keyword argument.
        colours=tuple(schema.colours),
        # Provides the `code_length` parameter or keyword argument.
        code_length=schema.code_length,
        # Provides the `max_attempts` parameter or keyword argument.
        max_attempts=schema.max_attempts,
        # Provides the `duplicates_allowed` parameter or keyword argument.
        duplicates_allowed=schema.duplicates_allowed,
        # Provides the `code_maker` parameter or keyword argument.
        code_maker=schema.code_maker,
        # Provides the `visibility` parameter or keyword argument.
        visibility=schema.visibility,
        # Provides the `ranked` parameter or keyword argument.
        ranked=False,
        # Provides the `time_bonus_cap` parameter or keyword argument.
        time_bonus_cap=schema.time_bonus_cap,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `resolve_config` callable and its typed interface.
def resolve_config(
    # Declares the typed `difficulty` data field.
    difficulty: str | None,
    # Declares the typed `custom` data field.
    custom: GameConfigSchema | None,
    # Completes the signature and declares the callable return type.
) -> tuple[GameConfig, str | None]:
    # Checks this condition before executing the nested branch.
    if difficulty:
        # Returns this result to the caller and ends the current function.
        return get_preset(difficulty), difficulty
    # Checks this condition before executing the nested branch.
    if custom:
        # Returns this result to the caller and ends the current function.
        return config_from_schema(custom), None
    # Raises this exception to report an invalid or failed operation.
    raise DomainError("MISSING_GAME_CONFIG", "Choose a difficulty or custom game settings.")


# Defines the `ensure_profile` callable and its typed interface.
async def ensure_profile(session: MongoSession, principal: AuthPrincipal) -> Profile:
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, principal.user_id)
    # Checks this condition before executing the nested branch.
    if profile is None:
        # Computes and stores `profile` for subsequent operations.
        profile = Profile(id=principal.user_id, is_anonymous=principal.is_anonymous)
        # Calls `session.add` with the supplied values.
        session.add(profile)
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Waits for this asynchronous operation to complete.
            await session.flush()
        # Handles the listed exception so failure remains controlled.
        except DuplicateKeyError:
            # Waits for this asynchronous operation to complete.
            await session.rollback()
            # Computes and stores `profile` for subsequent operations.
            profile = await session.get(Profile, principal.user_id)
            # Checks this condition before executing the nested branch.
            if profile is None:
                # Executes this statement as the next step in the surrounding logic.
                raise
    # Checks this alternative when previous conditions were false.
    elif profile.deleted_at is not None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(403, "ACCOUNT_DELETED", "This account has been deleted.")
    # Checks this condition before executing the nested branch.
    if profile.is_banned:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(403, "ACCOUNT_RESTRICTED", "This account is restricted.")
    # Checks this condition before executing the nested branch.
    if profile.is_anonymous and not principal.is_anonymous:
        # Computes and stores `profile.is_anonymous` for subsequent operations.
        profile.is_anonymous = False
    # Returns this result to the caller and ends the current function.
    return profile


# Defines the `_cipher_context` callable and its typed interface.
def _cipher_context(public_id: str) -> str:
    # Returns this result to the caller and ends the current function.
    return f"game:{public_id}:{RULE_SET_VERSION}"


# Defines the `_idempotency_reused` callable and its typed interface.
def _idempotency_reused() -> APIError:
    # Returns this result to the caller and ends the current function.
    return APIError(
        # Supplies this item to the surrounding call or collection.
        409,
        # Supplies this item to the surrounding call or collection.
        "IDEMPOTENCY_KEY_REUSED",
        # Supplies this item to the surrounding call or collection.
        "This idempotency key was already used with a different request.",
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_expected_game_config` callable and its typed interface.
def _expected_game_config(request: CreateGameRequest) -> tuple[GameConfig, str | None]:
    # Executes this statement as the next step in the surrounding logic.
    config, difficulty = resolve_config(request.difficulty, request.config)
    # Checks this condition before executing the nested branch.
    if request.mode in {GameMode.PRACTICE, GameMode.PASS_AND_PLAY}:
        # Computes and stores `config` for subsequent operations.
        config = GameConfig.from_dict(config.to_dict() | {"ranked": False})
    # Returns this result to the caller and ends the current function.
    return config, difficulty


# Defines the `_game_creation_matches` callable and its typed interface.
def _game_creation_matches(
    # Declares the typed `game` data field.
    game: GameSession,
    # Declares the typed `request` data field.
    request: CreateGameRequest,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Declares the typed `daily_id` data field.
    daily_id: uuid.UUID | None,
    # Declares the typed `friend_id` data field.
    friend_id: uuid.UUID | None,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID | None,
    # Completes the signature and declares the callable return type.
) -> bool:
    # Executes this statement as the next step in the surrounding logic.
    config, difficulty = _expected_game_config(request)
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        game.mode != request.mode.value
        # Executes this statement as the next step in the surrounding logic.
        or game.difficulty != difficulty
        # Executes this statement as the next step in the surrounding logic.
        or game.config != config.to_dict()
        # Executes this statement as the next step in the surrounding logic.
        or game.daily_challenge_id != daily_id
        # Executes this statement as the next step in the surrounding logic.
        or game.friend_challenge_id != friend_id
        # Executes this statement as the next step in the surrounding logic.
        or game.room_id != room_id
        # Begins the nested block or multiline expression completed below.
    ):
        # Returns this result to the caller and ends the current function.
        return False
    # Checks this condition before executing the nested branch.
    if request.secret is None:
        # Returns this result to the caller and ends the current function.
        return True
    # Computes and stores `requested_secret` for subsequent operations.
    requested_secret = validate_code(request.secret, config)
    # Computes and stores `stored_secret` for subsequent operations.
    stored_secret = cipher.decrypt(
        # Supplies this item to the surrounding call or collection.
        game.encrypted_secret,
        # Supplies this item to the surrounding call or collection.
        game.secret_nonce,
        # Supplies this item to the surrounding call or collection.
        game.secret_key_version,
        # Provides the `context` parameter or keyword argument.
        context=_cipher_context(game.public_id),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return stored_secret == requested_secret


# Defines the `_assert_game_creation_matches` callable and its typed interface.
def _assert_game_creation_matches(
    # Declares the typed `game` data field.
    game: GameSession,
    # Declares the typed `request` data field.
    request: CreateGameRequest,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Declares the typed `daily_id` data field.
    daily_id: uuid.UUID | None,
    # Declares the typed `friend_id` data field.
    friend_id: uuid.UUID | None,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID | None,
    # Completes the signature and declares the callable return type.
) -> None:
    # Checks this condition before executing the nested branch.
    if not _game_creation_matches(
        # Supplies this item to the surrounding call or collection.
        game,
        # Supplies this item to the surrounding call or collection.
        request,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `daily_id` parameter or keyword argument.
        daily_id=daily_id,
        # Provides the `friend_id` parameter or keyword argument.
        friend_id=friend_id,
        # Provides the `room_id` parameter or keyword argument.
        room_id=room_id,
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise _idempotency_reused()


# Defines the `load_owned_game` callable and its typed interface.
async def load_owned_game(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `public_id` data field.
    public_id: str,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `for_update` parameter or keyword argument.
    for_update: bool = False,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Stores `game` because later steps depend on this value.
    game = await session.find_one(
        # Supplies this required nested value.
        GameSession,
        {"public_id": public_id, "owner_id": principal.user_id},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if game is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "GAME_NOT_FOUND", "Game not found.")
    # Returns this result to the caller and ends the current function.
    return game


# Defines the `game_response` callable and its typed interface.
def game_response(game: GameSession, cipher: SecretCipher) -> GameResponse:
    # Computes and stores `terminal` for subsequent operations.
    terminal = GameStatus(game.status).terminal and game.mode != GameMode.DUEL.value
    # Computes and stores `secret` for subsequent operations.
    secret = None
    # Checks this condition before executing the nested branch.
    if terminal:
        # Computes and stores `secret` for subsequent operations.
        secret = list(
            # Calls `cipher.decrypt` with the supplied values.
            cipher.decrypt(
                # Supplies this item to the surrounding call or collection.
                game.encrypted_secret,
                # Supplies this item to the surrounding call or collection.
                game.secret_nonce,
                # Supplies this item to the surrounding call or collection.
                game.secret_key_version,
                # Provides the `context` parameter or keyword argument.
                context=_cipher_context(game.public_id),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Computes and stores `attempts` for subsequent operations.
    attempts = [
        # Calls `AttemptSchema` with the supplied values.
        AttemptSchema(
            # Provides the `number` parameter or keyword argument.
            number=attempt.attempt_number,
            # Provides the `guess` parameter or keyword argument.
            guess=attempt.guess,
            # Provides the `feedback` parameter or keyword argument.
            feedback=FeedbackSchema(black=attempt.black_pegs, white=attempt.white_pegs),
            # Provides the `submitted_at` parameter or keyword argument.
            submitted_at=attempt.submitted_at,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Iterates through the supplied values for the nested operation.
        for attempt in game.attempts
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Computes and stores `breakdown` for subsequent operations.
    breakdown = (
        # Calls `ScoreBreakdownSchema.model_validate` with the supplied values.
        ScoreBreakdownSchema.model_validate(game.score_breakdown) if game.score_breakdown else None
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return GameResponse(
        # Provides the `id` parameter or keyword argument.
        id=game.public_id,
        # Provides the `mode` parameter or keyword argument.
        mode=game.mode,
        # Provides the `status` parameter or keyword argument.
        status=game.status,
        # Provides the `difficulty` parameter or keyword argument.
        difficulty=game.difficulty,
        # Provides the `config` parameter or keyword argument.
        config=GameConfigSchema.model_validate(game.config),
        # Provides the `attempts` parameter or keyword argument.
        attempts=attempts,
        # Provides the `attempts_used` parameter or keyword argument.
        attempts_used=game.attempts_used,
        # Provides the `max_attempts` parameter or keyword argument.
        max_attempts=game.maximum_attempts,
        # Provides the `attempts_remaining` parameter or keyword argument.
        attempts_remaining=max(0, game.maximum_attempts - game.attempts_used),
        # Provides the `started_at` parameter or keyword argument.
        started_at=game.started_at,
        # Provides the `completed_at` parameter or keyword argument.
        completed_at=game.completed_at,
        # Provides the `score` parameter or keyword argument.
        score=game.final_score,
        # Provides the `score_breakdown` parameter or keyword argument.
        score_breakdown=breakdown,
        # Provides the `secret` parameter or keyword argument.
        secret=secret,
        # Provides the `ranked` parameter or keyword argument.
        ranked=game.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `create_game` callable and its typed interface.
async def create_game(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `request` data field.
    request: CreateGameRequest,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `secret_override` parameter or keyword argument.
    secret_override: tuple[str, ...] | None = None,
    # Provides the `daily_id` parameter or keyword argument.
    daily_id: uuid.UUID | None = None,
    # Provides the `friend_id` parameter or keyword argument.
    friend_id: uuid.UUID | None = None,
    # Provides the `room_id` parameter or keyword argument.
    room_id: uuid.UUID | None = None,
    # Provides the `linked_expires_at` parameter or keyword argument.
    linked_expires_at: datetime | None = None,
    # Provides the `commit` parameter or keyword argument.
    commit: bool = True,
    # Provides the `settings` parameter or keyword argument.
    settings: Settings | None = None,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `fingerprint` for subsequent operations.
    fingerprint = None
    # Checks this condition before executing the nested branch.
    if request.idempotency_key:
        # Computes and stores `fingerprint` for subsequent operations.
        fingerprint = creation_request_fingerprint(
            # Supplies this item to the surrounding call or collection.
            "game.create",
            # Uses the current HTTP request or response in this operation.
            request.model_dump(mode="json", by_alias=True, exclude={"idempotency_key"})
            # Begins the nested block or multiline expression completed below.
            | {
                # Associates the `dailyId` key with its value.
                "dailyId": str(daily_id) if daily_id else None,
                # Associates the `friendId` key with its value.
                "friendId": str(friend_id) if friend_id else None,
                # Associates the `roomId` key with its value.
                "roomId": str(room_id) if room_id else None,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Supplies this item to the surrounding call or collection.
            settings or get_settings(),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `existing` for subsequent operations.
        existing = await session.find_one(
            # Supplies this required nested value.
            GameSession,
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "owner_id": principal.user_id,
                # Supplies this literal value to the surrounding declaration or call.
                "creation_idempotency_key": request.idempotency_key,
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Checks this condition before executing the nested branch.
        if existing:
            # Checks this condition before executing the nested branch.
            if (
                # Executes this statement as the next step in the surrounding logic.
                existing.creation_request_fingerprint is not None
                # Executes this statement as the next step in the surrounding logic.
                and existing.creation_request_fingerprint != fingerprint
                # Begins the nested block or multiline expression completed below.
            ):
                # Raises this exception to report an invalid or failed operation.
                raise _idempotency_reused()
            # Calls `_assert_game_creation_matches` with the supplied values.
            _assert_game_creation_matches(
                # Supplies this item to the surrounding call or collection.
                existing,
                # Supplies this item to the surrounding call or collection.
                request,
                # Supplies this item to the surrounding call or collection.
                cipher,
                # Provides the `daily_id` parameter or keyword argument.
                daily_id=daily_id,
                # Provides the `friend_id` parameter or keyword argument.
                friend_id=friend_id,
                # Provides the `room_id` parameter or keyword argument.
                room_id=room_id,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Returns this result to the caller and ends the current function.
            return existing
    # Checks this condition before executing the nested branch.
    if request.mode in {GameMode.DAILY, GameMode.FRIEND_CHALLENGE, GameMode.DUEL} and not (
        # Executes this statement as the next step in the surrounding logic.
        daily_id or friend_id or room_id
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Executes this statement as the next step in the surrounding logic.
            400,
            # Supplies this string to the surrounding call or collection.
            "DEDICATED_ENDPOINT_REQUIRED",
            # Supplies this string to the surrounding call or collection.
            "Use the dedicated endpoint for this mode.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Executes this statement as the next step in the surrounding logic.
    config, difficulty = _expected_game_config(request)
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        config.code_maker is CodeMakerType.HUMAN
        # Executes this statement as the next step in the surrounding logic.
        and request.mode is not GameMode.PASS_AND_PLAY
        # Executes this statement as the next step in the surrounding logic.
        and friend_id is None
        # Executes this statement as the next step in the surrounding logic.
        and secret_override is None
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(400, "INVALID_CODE_MAKER", "Human Code Maker is available in pass-and-play.")
    # Checks this condition before executing the nested branch.
    if request.secret is not None:
        # Checks this condition before executing the nested branch.
        if config.code_maker is not CodeMakerType.HUMAN and not friend_id:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(
                # Executes this statement as the next step in the surrounding logic.
                400,
                # Supplies this string to the surrounding call or collection.
                "SECRET_NOT_ACCEPTED",
                # Supplies this string to the surrounding call or collection.
                "A secret is not accepted for this game mode.",
                # Closes the multiline call, declaration, or collection started above.
            )
        # Computes and stores `secret_code` for subsequent operations.
        secret_code = validate_code(request.secret, config)
    # Handles the remaining case not matched by earlier branches.
    else:
        # Computes and stores `secret_code` for subsequent operations.
        secret_code = secret_override or generate_secret(config)
    # Computes and stores `public_id` for subsequent operations.
    public_id = public_token()
    # Computes and stores `encrypted` for subsequent operations.
    encrypted = cipher.encrypt(secret_code, context=_cipher_context(public_id))
    # Computes and stores `started_at` for subsequent operations.
    started_at = utcnow()
    # Computes and stores `ranked` for subsequent operations.
    ranked = (
        # Executes this statement as the next step in the surrounding logic.
        config.ranked
        # Executes this statement as the next step in the surrounding logic.
        and request.mode in OFFICIAL_GAME_MODES
        # Executes this statement as the next step in the surrounding logic.
        and difficulty is not None
        # Executes this statement as the next step in the surrounding logic.
        and preset_name(config) == difficulty
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game` for subsequent operations.
    game = GameSession(
        # Provides the `public_id` parameter or keyword argument.
        public_id=public_id,
        # Provides the `creation_idempotency_key` parameter or keyword argument.
        creation_idempotency_key=request.idempotency_key,
        # Provides the `creation_request_fingerprint` parameter or keyword argument.
        creation_request_fingerprint=fingerprint,
        # Provides the `owner_id` parameter or keyword argument.
        owner_id=principal.user_id,
        # Provides the `mode` parameter or keyword argument.
        mode=request.mode.value,
        # Provides the `difficulty` parameter or keyword argument.
        difficulty=difficulty,
        # Provides the `config` parameter or keyword argument.
        config=config.to_dict(),
        # Provides the `status` parameter or keyword argument.
        status=GameStatus.ACTIVE.value,
        # Provides the `rule_set_version` parameter or keyword argument.
        rule_set_version=RULE_SET_VERSION,
        # Provides the `scoring_version` parameter or keyword argument.
        scoring_version=SCORING_VERSION,
        # Provides the `encrypted_secret` parameter or keyword argument.
        encrypted_secret=encrypted.ciphertext,
        # Provides the `secret_nonce` parameter or keyword argument.
        secret_nonce=encrypted.nonce,
        # Provides the `secret_key_version` parameter or keyword argument.
        secret_key_version=encrypted.key_version,
        # Provides the `attempts_used` parameter or keyword argument.
        attempts_used=0,
        # Provides the `maximum_attempts` parameter or keyword argument.
        maximum_attempts=config.max_attempts,
        # Provides the `started_at` parameter or keyword argument.
        started_at=started_at,
        # Computes and stores `expires_at` for subsequent operations.
        expires_at=game_expiry_for_mode(
            # Uses the current HTTP request or response in this operation.
            request.mode,
            # Supplies this item to the surrounding call or collection.
            started_at,
            # Provides the `linked_expires_at` parameter or keyword argument.
            linked_expires_at=linked_expires_at,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Computes and stores `ranked_eligibility` for subsequent operations.
        ranked_eligibility=(
            # Executes this statement as the next step in the surrounding logic.
            LeaderboardEligibility.ELIGIBLE.value
            # Checks this condition before executing the nested branch.
            if ranked
            # Executes this statement as the next step in the surrounding logic.
            else LeaderboardEligibility.UNRANKED.value
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Provides the `daily_challenge_id` parameter or keyword argument.
        daily_challenge_id=daily_id,
        # Provides the `friend_challenge_id` parameter or keyword argument.
        friend_challenge_id=friend_id,
        # Provides the `room_id` parameter or keyword argument.
        room_id=room_id,
        # Provides the `attempts` parameter or keyword argument.
        attempts=[],
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `session.add` with the supplied values.
    session.add(game)
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await session.flush()
    # Handles the listed exception so failure remains controlled.
    except DuplicateKeyError:
        # Waits for this asynchronous operation to complete.
        await session.rollback()
        # Computes and stores `identity_filter` for subsequent operations.
        identity_filter: dict[str, object] | None = None
        # Checks this condition before executing the nested branch.
        if request.idempotency_key:
            # Executes this statement as the next step in the surrounding logic.
            identity_filter = {"creation_idempotency_key": request.idempotency_key}
        # Checks this alternative when previous conditions were false.
        elif daily_id is not None:
            # Executes this statement as the next step in the surrounding logic.
            identity_filter = {"daily_challenge_id": daily_id}
        # Checks this alternative when previous conditions were false.
        elif friend_id is not None:
            # Executes this statement as the next step in the surrounding logic.
            identity_filter = {"friend_challenge_id": friend_id}
        # Checks this alternative when previous conditions were false.
        elif room_id is not None:
            # Executes this statement as the next step in the surrounding logic.
            identity_filter = {"room_id": room_id}
        # Checks this condition before executing the nested branch.
        if identity_filter is not None:
            # Computes and stores `concurrent_game` for subsequent operations.
            concurrent_game = await session.find_one(
                # Supplies this required nested value.
                GameSession,
                {"owner_id": principal.user_id, **identity_filter},
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Checks this condition before executing the nested branch.
            if concurrent_game:
                # Checks this condition before executing the nested branch.
                if request.idempotency_key:
                    # Checks this condition before executing the nested branch.
                    if (
                        # Executes this statement as the next step in the surrounding logic.
                        concurrent_game.creation_request_fingerprint is not None
                        # Executes this statement as the next step in the surrounding logic.
                        and concurrent_game.creation_request_fingerprint != fingerprint
                        # Begins the nested block or multiline expression completed below.
                    ):
                        # Raises this exception to report an invalid or failed operation.
                        raise _idempotency_reused() from None
                    # Calls `_assert_game_creation_matches` with the supplied values.
                    _assert_game_creation_matches(
                        # Supplies this item to the surrounding call or collection.
                        concurrent_game,
                        # Supplies this item to the surrounding call or collection.
                        request,
                        # Supplies this item to the surrounding call or collection.
                        cipher,
                        # Provides the `daily_id` parameter or keyword argument.
                        daily_id=daily_id,
                        # Provides the `friend_id` parameter or keyword argument.
                        friend_id=friend_id,
                        # Provides the `room_id` parameter or keyword argument.
                        room_id=room_id,
                        # Closes the multiline call, declaration, or collection started above.
                    )
                # Returns this result to the caller and ends the current function.
                return concurrent_game
        # Executes this statement as the next step in the surrounding logic.
        raise
    # Checks this condition before executing the nested branch.
    if commit:
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Returns this result to the caller and ends the current function.
    return game


# Defines the `submit_attempt` callable and its typed interface.
async def submit_attempt(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `game_id` data field.
    game_id: str,
    # Declares the typed `guess` data field.
    guess: list[str],
    # Declares the typed `idempotency_key` data field.
    idempotency_key: str,
    # Declares the typed `request_id` data field.
    request_id: str,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `commit` parameter or keyword argument.
    commit: bool = True,
    # Provides the `allow_duel` parameter or keyword argument.
    allow_duel: bool = False,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Computes and stores `game` for subsequent operations.
    game = await load_owned_game(session, game_id, principal, for_update=True)
    # Computes and stores `previous` for subsequent operations.
    previous = next(
        # Executes this statement as the next step in the surrounding logic.
        (attempt for attempt in game.attempts if attempt.idempotency_key == idempotency_key),
        # Supplies this item to the surrounding call or collection.
        None,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if previous:
        # Checks this condition before executing the nested branch.
        if tuple(previous.guess) != tuple(item.upper() for item in guess):
            # Raises this exception to report an invalid or failed operation.
            raise APIError(
                # Supplies this item to the surrounding call or collection.
                409,
                # Supplies this item to the surrounding call or collection.
                "IDEMPOTENCY_KEY_REUSED",
                # Supplies this item to the surrounding call or collection.
                "This idempotency key was already used for a different guess.",
                # Closes the multiline call, declaration, or collection started above.
            )
        # Returns this result to the caller and ends the current function.
        return game
    # Checks this condition before executing the nested branch.
    if game.mode == GameMode.DUEL.value and not allow_duel:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(409, "REALTIME_ENDPOINT_REQUIRED", "Submit duel guesses in the live room.")
    # Checks this condition before executing the nested branch.
    if expire_game_record(game, now=utcnow()):
        # Waits for this asynchronous operation to complete.
        await session.flush()
        # Checks this condition before executing the nested branch.
        if commit:
            # Waits for this asynchronous operation to complete.
            await session.commit()
        # Raises this exception to report an invalid or failed operation.
        raise APIError(410, "GAME_EXPIRED", "This game has expired.")
    # Checks this condition before executing the nested branch.
    if game.status != GameStatus.ACTIVE.value:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(409, "GAME_NOT_ACTIVE", "This game no longer accepts attempts.")
    # Computes and stores `config` for subsequent operations.
    config = GameConfig.from_dict(game.config)
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `normalized_guess` for subsequent operations.
        normalized_guess = validate_code(guess, config)
    # Handles the listed exception so failure remains controlled.
    except DomainError:
        # Executes this statement as the next step in the surrounding logic.
        game.invalid_submission_count += 1
        # Waits for this asynchronous operation to complete.
        await session.commit()
        # Executes this statement as the next step in the surrounding logic.
        raise
    # Computes and stores `secret_code` for subsequent operations.
    secret_code = cipher.decrypt(
        # Supplies this item to the surrounding call or collection.
        game.encrypted_secret,
        # Supplies this item to the surrounding call or collection.
        game.secret_nonce,
        # Supplies this item to the surrounding call or collection.
        game.secret_key_version,
        # Provides the `context` parameter or keyword argument.
        context=_cipher_context(game.public_id),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `feedback` for subsequent operations.
    feedback = calculate_feedback(secret_code, normalized_guess)
    # Computes and stores `now` for subsequent operations.
    now = utcnow()
    # Checks this condition before executing the nested branch.
    if game.mode == GameMode.DAILY.value and game.attempts_used == 0:
        # Computes and stores `game.started_at` for subsequent operations.
        game.started_at = now
    # Executes this statement as the next step in the surrounding logic.
    game.attempts_used += 1
    # Computes and stores `attempt` for subsequent operations.
    attempt = GameAttempt(
        # Provides the `game_id` parameter or keyword argument.
        game_id=game.id,
        # Provides the `attempt_number` parameter or keyword argument.
        attempt_number=game.attempts_used,
        # Provides the `guess` parameter or keyword argument.
        guess=list(normalized_guess),
        # Provides the `black_pegs` parameter or keyword argument.
        black_pegs=feedback.black,
        # Provides the `white_pegs` parameter or keyword argument.
        white_pegs=feedback.white,
        # Provides the `submitted_at` parameter or keyword argument.
        submitted_at=now,
        # Provides the `idempotency_key` parameter or keyword argument.
        idempotency_key=idempotency_key,
        # Provides the `request_id` parameter or keyword argument.
        request_id=request_id,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `game.attempts.append` with the supplied values.
    game.attempts.append(attempt)
    # Checks this condition before executing the nested branch.
    if feedback.black == config.code_length:
        # Computes and stores `game.status` for subsequent operations.
        game.status = GameStatus.WON.value
    # Checks this alternative when previous conditions were false.
    elif game.attempts_used >= game.maximum_attempts:
        # Computes and stores `game.status` for subsequent operations.
        game.status = GameStatus.LOST.value
    # Checks this condition before executing the nested branch.
    if GameStatus(game.status).terminal:
        # Computes and stores `game.completed_at` for subsequent operations.
        game.completed_at = now
        # Computes and stores `game.elapsed_seconds` for subsequent operations.
        game.elapsed_seconds = max(0, int((now - ensure_aware(game.started_at)).total_seconds()))
        # Computes and stores `breakdown` for subsequent operations.
        breakdown = calculate_score(
            # Supplies this item to the surrounding call or collection.
            config,
            # Provides the `status` parameter or keyword argument.
            status=GameStatus(game.status),
            # Provides the `attempts_used` parameter or keyword argument.
            attempts_used=game.attempts_used,
            # Provides the `elapsed_seconds` parameter or keyword argument.
            elapsed_seconds=game.elapsed_seconds,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `game.final_score` for subsequent operations.
        game.final_score = breakdown.total
        # Computes and stores `game.score_breakdown` for subsequent operations.
        game.score_breakdown = breakdown.to_dict()
        # Waits for this asynchronous operation to complete.
        await _finalize_game(session, game, principal)
    # Waits for this asynchronous operation to complete.
    await session.flush()
    # Checks this condition before executing the nested branch.
    if commit:
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Returns this result to the caller and ends the current function.
    return game


# Defines the `abandon` callable and its typed interface.
async def abandon(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `game_id` data field.
    game_id: str,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `room_events` parameter or keyword argument.
    room_events: list[tuple[str, dict[str, object]]] | None = None,
    # Completes the signature and declares the callable return type.
) -> GameResponse:
    # Computes and stores `game` for subsequent operations.
    game = await load_owned_game(session, game_id, principal)
    # Checks this condition before executing the nested branch.
    if game.mode == GameMode.DUEL.value and game.room_id is not None:
        # Realtime submissions and finalizers lock room -> games. Preserve that
        # global order for HTTP abandonment so cross-player operations cannot
        # deadlock while each holds a different game row.
        # Waits for this asynchronous operation to complete.
        await load_room_for_member(session, game.room_id, principal, for_update=True)
    # Computes and stores `game` for subsequent operations.
    game = await load_owned_game(session, game_id, principal, for_update=True)
    # Checks this condition before executing the nested branch.
    if expire_game_record(game, now=utcnow()):
        # Waits for this asynchronous operation to complete.
        await session.commit()
        # Raises this exception to report an invalid or failed operation.
        raise APIError(410, "GAME_EXPIRED", "This game has expired.")
    # Checks this condition before executing the nested branch.
    if game.status != GameStatus.ACTIVE.value:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(409, "GAME_NOT_ACTIVE", "This game is already complete.")
    # Computes and stores `game.status` for subsequent operations.
    game.status = GameStatus.ABANDONED.value
    # Computes and stores `game.completed_at` for subsequent operations.
    game.completed_at = utcnow()
    # Computes and stores `game.elapsed_seconds` for subsequent operations.
    game.elapsed_seconds = max(
        # Executes this statement as the next step in the surrounding logic.
        0,
        # Calls `int` with these supplied values.
        int((game.completed_at - ensure_aware(game.started_at)).total_seconds()),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `breakdown` for subsequent operations.
    breakdown = calculate_score(
        # Calls `GameConfig.from_dict` with the supplied values.
        GameConfig.from_dict(game.config),
        # Provides the `status` parameter or keyword argument.
        status=GameStatus.ABANDONED,
        # Provides the `attempts_used` parameter or keyword argument.
        attempts_used=game.attempts_used,
        # Provides the `elapsed_seconds` parameter or keyword argument.
        elapsed_seconds=game.elapsed_seconds,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `game.final_score` for subsequent operations.
    game.final_score = 0
    # Computes and stores `game.score_breakdown` for subsequent operations.
    game.score_breakdown = breakdown.to_dict()
    # Computes and stores `game.ranked_eligibility` for subsequent operations.
    game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
    # Checks this condition before executing the nested branch.
    if game.mode == GameMode.DUEL.value and game.room_id is not None:
        # Computes and stores `room` for subsequent operations.
        room = await session.get(MultiplayerRoom, game.room_id)
        # Checks this condition before executing the nested branch.
        if room and room.status in {"waiting", "active"}:
            # Computes and stores `other_game` for subsequent operations.
            other_game = await session.find_one(
                # Supplies this required nested value.
                GameSession,
                # Supplies this required nested value.
                {"room_id": room.id, "owner_id": {"$ne": principal.user_id}},
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Checks this condition before executing the nested branch.
            if room.status == "active" and other_game is not None:
                # Computes and stores `room.winner_id` for subsequent operations.
                room.winner_id = other_game.owner_id
                # Computes and stores `room.winner_at` for subsequent operations.
                room.winner_at = game.completed_at
                # Computes and stores `room.is_tie` for subsequent operations.
                room.is_tie = False
                # Computes and stores `room.status` for subsequent operations.
                room.status = "completed"
                # Checks this condition before executing the nested branch.
                if other_game.status == GameStatus.ACTIVE.value:
                    # Computes and stores `other_game.status` for subsequent operations.
                    other_game.status = GameStatus.ABANDONED.value
                    # Computes and stores `other_game.completed_at` for subsequent operations.
                    other_game.completed_at = game.completed_at
                    # Computes and stores `other_game.elapsed_seconds` for subsequent operations.
                    other_game.elapsed_seconds = max(
                        # Supplies this item to the surrounding call or collection.
                        0,
                        # Calls `int` with the supplied values.
                        int(
                            # Begins the nested block or multiline expression completed below.
                            (
                                # Executes this statement as the next step in the surrounding logic.
                                game.completed_at - ensure_aware(other_game.started_at)
                                # Executes this statement as the next step in the surrounding logic.
                            ).total_seconds()
                            # Closes the multiline call, declaration, or collection started above.
                        ),
                        # Closes the multiline call, declaration, or collection started above.
                    )
                    # Computes and stores `other_game.final_score` for subsequent operations.
                    other_game.final_score = 0
                    # Computes and stores `other_game.score_breakdown` for subsequent operations.
                    other_game.score_breakdown = calculate_score(
                        # Calls `GameConfig.from_dict` with the supplied values.
                        GameConfig.from_dict(other_game.config),
                        # Provides the `status` parameter or keyword argument.
                        status=GameStatus.ABANDONED,
                        # Provides the `attempts_used` parameter or keyword argument.
                        attempts_used=other_game.attempts_used,
                        # Provides the `elapsed_seconds` parameter or keyword argument.
                        elapsed_seconds=other_game.elapsed_seconds,
                        # Executes this statement as the next step in the surrounding logic.
                    ).to_dict()
                    # Computes and stores `other_game.ranked_eligibility` for subsequent operations.
                    other_game.ranked_eligibility = LeaderboardEligibility.UNRANKED.value
                # Computes and stores `completion_event` for subsequent operations.
                completion_event = await record_room_completion(session, room, "forfeit")
            # Handles the remaining case not matched by earlier branches.
            else:
                # Computes and stores `room.status` for subsequent operations.
                room.status = "terminated"
                # Computes and stores `completion_event` for subsequent operations.
                completion_event = await record_room_completion(session, room, "terminated")
            # Checks this condition before executing the nested branch.
            if completion_event is not None and room_events is not None:
                # Calls `room_events.append` with the supplied values.
                room_events.append((str(room.id), completion_event))
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return game_response(game, cipher)


# Defines the `_finalize_game` callable and its typed interface.
async def _finalize_game(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `game` data field.
    game: GameSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, principal.user_id)
    # Computes and stores `settings` for subsequent operations.
    settings = get_settings()
    # Checks this condition before executing the nested branch.
    if (
        # Waits for this asynchronous operation to complete.
        await feature_enabled(session, settings, "leaderboards")
        # Executes this statement as the next step in the surrounding logic.
        and game.status == GameStatus.WON.value
        # Executes this statement as the next step in the surrounding logic.
        and game.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value
        # Executes this statement as the next step in the surrounding logic.
        and profile
        # Executes this statement as the next step in the surrounding logic.
        and not profile.is_anonymous
        # Executes this statement as the next step in the surrounding logic.
        and profile.public_leaderboards
        # Begins the nested block or multiline expression completed below.
    ):
        # Computes and stores `category` for subsequent operations.
        category = (
            # Executes this statement as the next step in the surrounding logic.
            f"daily:{game.daily_challenge_id}" if game.daily_challenge_id else game.difficulty
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `session.add` with the supplied values.
        session.add(
            # Calls `LeaderboardEntry` with the supplied values.
            LeaderboardEntry(
                # Provides the `game_id` parameter or keyword argument.
                game_id=game.id,
                # Provides the `user_id` parameter or keyword argument.
                user_id=principal.user_id,
                # Provides the `category` parameter or keyword argument.
                category=category or "official",
                # Provides the `score` parameter or keyword argument.
                score=game.final_score or 0,
                # Provides the `attempts_used` parameter or keyword argument.
                attempts_used=game.attempts_used,
                # Provides the `elapsed_seconds` parameter or keyword argument.
                elapsed_seconds=game.elapsed_seconds or 0,
                # Provides the `completed_at` parameter or keyword argument.
                completed_at=game.completed_at or utcnow(),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Checks this condition before executing the nested branch.
    if (
        # Waits for this asynchronous operation to complete.
        await feature_enabled(session, settings, "achievements")
        # Executes this statement as the next step in the surrounding logic.
        and profile is not None
        # Executes this statement as the next step in the surrounding logic.
        and not profile.is_anonymous
        # Executes this statement as the next step in the surrounding logic.
        and game.mode not in {GameMode.PRACTICE.value, GameMode.PASS_AND_PLAY.value}
        # Begins the nested block or multiline expression completed below.
    ):
        # Waits for this asynchronous operation to complete.
        await _award_achievements(session, game, principal.user_id)


# Defines the `_award_achievements` callable and its typed interface.
async def _award_achievements(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `game` data field.
    game: GameSession,
    # Declares the typed `user_id` data field.
    user_id: uuid.UUID,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `keys` for subsequent operations.
    keys: set[str] = set()
    # Checks this condition before executing the nested branch.
    if game.status == GameStatus.WON.value and game.attempts_used == game.maximum_attempts:
        # Calls `keys.add` with the supplied values.
        keys.add("comeback")
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        game.status == GameStatus.WON.value
        # Executes this statement as the next step in the surrounding logic.
        and game.ranked_eligibility == LeaderboardEligibility.ELIGIBLE.value
        # Executes this statement as the next step in the surrounding logic.
        and game.mode in {GameMode.SOLO.value, GameMode.DAILY.value}
        # Begins the nested block or multiline expression completed below.
    ):
        # Computes and stores `won_count` for subsequent operations.
        won_count = await session.count(
            # Supplies this required nested value.
            GameSession,
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "owner_id": user_id,
                # Supplies this literal value to the surrounding declaration or call.
                "status": GameStatus.WON.value,
                # Supplies this literal value to the surrounding declaration or call.
                "mode": {"$in": [GameMode.SOLO.value, GameMode.DAILY.value]},
                # Supplies this literal value to the surrounding declaration or call.
                "ranked_eligibility": LeaderboardEligibility.ELIGIBLE.value,
                # Supplies this literal value to the surrounding declaration or call.
                "_id": {"$ne": game.id},
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Checks this condition before executing the nested branch.
        if not won_count:
            # Calls `keys.add` with the supplied values.
            keys.add("first_break")
        # Checks this condition before executing the nested branch.
        if game.attempts_used == 1:
            # Calls `keys.add` with the supplied values.
            keys.add("one_shot")
        # Checks this condition before executing the nested branch.
        if game.invalid_submission_count == 0:
            # Calls `keys.add` with the supplied values.
            keys.add("no_waste")
        # Checks this condition before executing the nested branch.
        if game.difficulty == "hard":
            # Calls `keys.add` with the supplied values.
            keys.add("hard_mode")
        # Checks this condition before executing the nested branch.
        if game.difficulty == "expert":
            # Calls `keys.add` with the supplied values.
            keys.add("expert_breaker")
    # Checks this condition before executing the nested branch.
    if game.mode == GameMode.DAILY.value and GameStatus(game.status).terminal:
        # Calls `keys.add` with the supplied values.
        keys.add("daily_debut")
        # Computes and stores `prior_daily_completions` for subsequent operations.
        daily_rows = await session.aggregate(
            # Supplies this required nested value.
            GameSession,
            # Supplies this required nested value.
            [
                # Supplies this required nested value.
                {
                    # Supplies this literal value to the surrounding declaration or call.
                    "$match": {
                        # Supplies this literal value to the surrounding declaration or call.
                        "owner_id": user_id,
                        # Supplies this literal value to the surrounding declaration or call.
                        "mode": GameMode.DAILY.value,
                        # Supplies this literal value to the surrounding declaration or call.
                        "completed_at": {"$ne": None},
                        # Supplies this literal value to the surrounding declaration or call.
                        "_id": {"$ne": game.id},
                        # Closes the multiline declaration, call, or collection opened above.
                    }
                    # Closes the multiline declaration, call, or collection opened above.
                },
                # Supplies this required nested value.
                {"$group": {"_id": "$daily_challenge_id"}},
                # Supplies this required nested value.
                {"$count": "total"},
                # Closes the multiline declaration, call, or collection opened above.
            ],
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Stores `prior_daily_completions` because later steps depend on this value.
        prior_daily_completions = daily_rows[0]["total"] if daily_rows else 0
        # Checks this condition before executing the nested branch.
        if (prior_daily_completions or 0) + 1 >= 7:
            # Calls `keys.add` with the supplied values.
            keys.add("logic_week")
    # Checks this condition before executing the nested branch.
    if game.mode == GameMode.FRIEND_CHALLENGE.value and GameStatus(game.status).terminal:
        # Calls `keys.add` with the supplied values.
        keys.add("challenger")
    # Iterates through the supplied values for the nested operation.
    for key in keys:
        # Stores `award` because later steps depend on this value.
        award = UserAchievement(user_id=user_id, achievement_key=key, game_id=game.id)
        # Performs this required operation before the surrounding flow continues.
        await session.upsert_one(
            # Supplies this required nested value.
            UserAchievement,
            # Supplies this required nested value.
            {"user_id": user_id, "achievement_key": key},
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "$setOnInsert": {
                    # Supplies this literal value to the surrounding declaration or call.
                    "_id": award.id,
                    # Supplies this literal value to the surrounding declaration or call.
                    "user_id": user_id,
                    # Supplies this literal value to the surrounding declaration or call.
                    "achievement_key": key,
                    # Supplies this literal value to the surrounding declaration or call.
                    "awarded_at": award.awarded_at,
                    # Supplies this literal value to the surrounding declaration or call.
                    "game_id": game.id,
                    # Closes the multiline declaration, call, or collection opened above.
                }
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Closes the multiline declaration, call, or collection opened above.
        )


# Defines the `get_or_create_daily` callable and its typed interface.
async def get_or_create_daily(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Provides the `challenge_date` parameter or keyword argument.
    challenge_date: date | None = None,
    # Completes the signature and declares the callable return type.
) -> DailyChallenge:
    # Computes and stores `day` for subsequent operations.
    day = challenge_date or utcnow().date()
    # Computes and stores `existing` for subsequent operations.
    existing = await session.find_one(
        # Supplies this required nested value.
        DailyChallenge,
        # Supplies this required nested value.
        {"challenge_date": day, "rule_set_version": RULE_SET_VERSION},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if existing:
        # Returns this result to the caller and ends the current function.
        return existing
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `daily_keys` for subsequent operations.
        daily_keys = settings.daily_hmac_keyring()
        # Computes and stores `active_key_version` for subsequent operations.
        active_key_version = settings.daily_hmac_active_key_version
        # Executes this statement as the next step in the surrounding logic.
        daily_keys[active_key_version]
    # Handles the listed exception so failure remains controlled.
    except (KeyError, ValueError):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Executes this statement as the next step in the surrounding logic.
            503,
            # Supplies this string to the surrounding call or collection.
            "DAILY_UNAVAILABLE",
            # Supplies this string to the surrounding call or collection.
            "The daily challenge is temporarily unavailable.",
            # Executes this statement as the next step in the surrounding logic.
        ) from None
    # Computes and stores `config` for subsequent operations.
    config = get_preset("normal")
    # Computes and stores `public_id` for subsequent operations.
    public_id = daily_challenge_id(day)
    # Computes and stores `daily` for subsequent operations.
    daily = DailyChallenge(
        # Provides the `challenge_date` parameter or keyword argument.
        challenge_date=day,
        # Provides the `public_id` parameter or keyword argument.
        public_id=public_id,
        # Provides the `config` parameter or keyword argument.
        config=config.to_dict(),
        # Provides the `derivation_version` parameter or keyword argument.
        derivation_version=DAILY_DERIVATION_VERSION,
        # Provides the `derivation_key_version` parameter or keyword argument.
        derivation_key_version=active_key_version,
        # Provides the `rule_set_version` parameter or keyword argument.
        rule_set_version=RULE_SET_VERSION,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `session.add` with the supplied values.
    session.add(daily)
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Handles the listed exception so failure remains controlled.
    except DuplicateKeyError:
        # Waits for this asynchronous operation to complete.
        await session.rollback()
        # Computes and stores `concurrent` for subsequent operations.
        concurrent = await session.find_one(
            # Supplies this required nested value.
            DailyChallenge,
            # Supplies this required nested value.
            {"challenge_date": day, "rule_set_version": RULE_SET_VERSION},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Checks this condition before executing the nested branch.
        if concurrent:
            # Returns this result to the caller and ends the current function.
            return concurrent
        # Executes this statement as the next step in the surrounding logic.
        raise
    # Returns this result to the caller and ends the current function.
    return daily


# Defines the `start_daily` callable and its typed interface.
async def start_daily(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `practice` parameter or keyword argument.
    practice: bool = False,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `daily` for subsequent operations.
    daily = await get_or_create_daily(session, settings, cipher)
    # Computes and stores `existing` for subsequent operations.
    existing = await session.find_one(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {"owner_id": principal.user_id, "daily_challenge_id": daily.id},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if existing is not None and expire_game_record(existing, now=utcnow()):
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Checks this condition before executing the nested branch.
    if existing and (existing.status == GameStatus.ACTIVE.value or not practice):
        # Returns this result to the caller and ends the current function.
        return existing
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Computes and stores `derivation_key` for subsequent operations.
        derivation_key = settings.daily_hmac_keyring()[daily.derivation_key_version]
    # Handles the listed exception so failure remains controlled.
    except (KeyError, ValueError):
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Executes this statement as the next step in the surrounding logic.
            503,
            # Supplies this string to the surrounding call or collection.
            "DAILY_UNAVAILABLE",
            # Supplies this string to the surrounding call or collection.
            "The daily challenge is temporarily unavailable.",
            # Executes this statement as the next step in the surrounding logic.
        ) from None
    # Computes and stores `secret_code` for subsequent operations.
    secret_code = derive_daily_secret(
        # Supplies this item to the surrounding call or collection.
        daily.challenge_date,
        # Calls `GameConfig.from_dict` with the supplied values.
        GameConfig.from_dict(daily.config),
        # Supplies this item to the surrounding call or collection.
        derivation_key,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `request` for subsequent operations.
    request = CreateGameRequest(
        # Provides the `mode` parameter or keyword argument.
        mode=GameMode.PRACTICE if practice else GameMode.DAILY,
        # Provides the `difficulty` parameter or keyword argument.
        difficulty="normal",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return await create_game(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        request,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `secret_override` parameter or keyword argument.
        secret_override=secret_code,
        # Provides the `daily_id` parameter or keyword argument.
        daily_id=None if practice else daily.id,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `create_challenge` callable and its typed interface.
async def create_challenge(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `request` data field.
    request: CreateChallengeRequest,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> tuple[FriendChallenge, str]:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Waits for this asynchronous operation to complete.
    await session.get(Profile, principal.user_id)
    # Computes and stores `fingerprint` for subsequent operations.
    fingerprint = (
        # Calls `creation_request_fingerprint` with the supplied values.
        creation_request_fingerprint(
            # Supplies this item to the surrounding call or collection.
            "challenge.create",
            # Uses the current HTTP request or response in this operation.
            request.model_dump(mode="json", by_alias=True, exclude={"idempotency_key"}),
            # Supplies this item to the surrounding call or collection.
            settings,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Checks this condition before executing the nested branch.
        if request.idempotency_key
        # Executes this statement as the next step in the surrounding logic.
        else None
        # Closes the multiline call, declaration, or collection started above.
    )

    # Defines the `expected_payload` callable and its typed interface.
    def expected_payload() -> tuple[GameConfig, tuple[str, ...] | None]:
        # Executes this statement as the next step in the surrounding logic.
        expected_config, _ = resolve_config(request.difficulty, request.config)
        # Computes and stores `expected_config` for subsequent operations.
        expected_config = GameConfig.from_dict(
            # Calls `expected_config.to_dict` with the supplied values.
            expected_config.to_dict()
            # Begins the nested block or multiline expression completed below.
            | {
                # Associates the `ranked` key with its value.
                "ranked": False,
                # Associates the `visibility` key with its value.
                "visibility": "shareable",
                # Associates the `codeMaker` key with its value.
                "codeMaker": "human" if request.secret else "computer",
                # Closes the multiline call, declaration, or collection started above.
            }
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `expected_secret` for subsequent operations.
        expected_secret = validate_code(request.secret, expected_config) if request.secret else None
        # Returns this result to the caller and ends the current function.
        return expected_config, expected_secret

    # Defines the `assert_same_payload` callable and its typed interface.
    def assert_same_payload(existing: FriendChallenge) -> None:
        # Executes this statement as the next step in the surrounding logic.
        expected_config, expected_secret = expected_payload()
        # Checks this condition before executing the nested branch.
        if (
            # Executes this statement as the next step in the surrounding logic.
            existing.title != request.title
            # Executes this statement as the next step in the surrounding logic.
            or existing.show_creator_name != request.show_creator_name
            # Executes this statement as the next step in the surrounding logic.
            or existing.config != expected_config.to_dict()
            # Begins the nested block or multiline expression completed below.
        ):
            # Raises this exception to report an invalid or failed operation.
            raise _idempotency_reused()
        # Checks this condition before executing the nested branch.
        if expected_secret is not None:
            # Computes and stores `stored_secret` for subsequent operations.
            stored_secret = cipher.decrypt(
                # Supplies this item to the surrounding call or collection.
                existing.encrypted_secret,
                # Supplies this item to the surrounding call or collection.
                existing.secret_nonce,
                # Supplies this item to the surrounding call or collection.
                existing.secret_key_version,
                # Provides the `context` parameter or keyword argument.
                context=f"challenge:{existing.share_code_hash}:{RULE_SET_VERSION}",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Checks this condition before executing the nested branch.
            if stored_secret != expected_secret:
                # Raises this exception to report an invalid or failed operation.
                raise _idempotency_reused()

    # Checks this condition before executing the nested branch.
    if request.idempotency_key:
        # Computes and stores `share_code` for subsequent operations.
        share_code = idempotent_invite_code(
            # Executes this statement as the next step in the surrounding logic.
            "friend",
            # Supplies this item to the surrounding call or collection.
            principal.user_id,
            # Supplies this item to the surrounding call or collection.
            request.idempotency_key,
            # Supplies this item to the surrounding call or collection.
            settings,
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `existing` for subsequent operations.
        existing = await session.find_one(
            # Supplies this required nested value.
            FriendChallenge,
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "creator_id": principal.user_id,
                # Supplies this literal value to the surrounding declaration or call.
                "creation_idempotency_key": request.idempotency_key,
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Checks this condition before executing the nested branch.
        if existing:
            # Checks this condition before executing the nested branch.
            if (
                # Executes this statement as the next step in the surrounding logic.
                existing.creation_request_fingerprint is not None
                # Executes this statement as the next step in the surrounding logic.
                and existing.creation_request_fingerprint != fingerprint
                # Begins the nested block or multiline expression completed below.
            ):
                # Raises this exception to report an invalid or failed operation.
                raise _idempotency_reused()
            # Calls `assert_same_payload` with the supplied values.
            assert_same_payload(existing)
            # Returns this result to the caller and ends the current function.
            return existing, share_code
    # Computes and stores `active_challenges` for subsequent operations.
    active_challenges = await session.count(
        # Supplies this required nested value.
        FriendChallenge,
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            "creator_id": principal.user_id,
            # Supplies this literal value to the surrounding declaration or call.
            "revoked_at": None,
            # Supplies this literal value to the surrounding declaration or call.
            "expires_at": {"$gt": utcnow()},
            # Closes the multiline declaration, call, or collection opened above.
        },
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Computes and stores `challenge_limit` for subsequent operations.
    challenge_limit = (
        # Executes this statement as the next step in the surrounding logic.
        MAX_ACTIVE_GUEST_CHALLENGES if principal.is_anonymous else MAX_ACTIVE_CHALLENGES_PER_USER
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if (active_challenges or 0) >= challenge_limit:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(
            # Supplies this item to the surrounding call or collection.
            409,
            # Supplies this item to the surrounding call or collection.
            "CHALLENGE_LIMIT_REACHED",
            # Supplies this item to the surrounding call or collection.
            "Revoke an active challenge before creating another one.",
            # Closes the multiline call, declaration, or collection started above.
        )
    # Executes this statement as the next step in the surrounding logic.
    config, requested_secret = expected_payload()
    # Computes and stores `secret_code` for subsequent operations.
    secret_code = requested_secret or generate_secret(config)
    # Computes and stores `share_code` for subsequent operations.
    share_code = (
        # Calls `idempotent_invite_code` with the supplied values.
        idempotent_invite_code("friend", principal.user_id, request.idempotency_key, settings)
        # Checks this condition before executing the nested branch.
        if request.idempotency_key
        # Executes this statement as the next step in the surrounding logic.
        else public_token(18)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `share_code_hash` for subsequent operations.
    share_code_hash = identifier_hash(share_code, settings)
    # Computes and stores `context` for subsequent operations.
    context = f"challenge:{share_code_hash}:{RULE_SET_VERSION}"
    # Computes and stores `encrypted` for subsequent operations.
    encrypted = cipher.encrypt(secret_code, context=context)
    # Computes and stores `challenge` for subsequent operations.
    challenge = FriendChallenge(
        # Provides the `share_code_hash` parameter or keyword argument.
        share_code_hash=share_code_hash,
        # Provides the `creation_idempotency_key` parameter or keyword argument.
        creation_idempotency_key=request.idempotency_key,
        # Provides the `creation_request_fingerprint` parameter or keyword argument.
        creation_request_fingerprint=fingerprint,
        # Provides the `creator_id` parameter or keyword argument.
        creator_id=principal.user_id,
        # Provides the `title` parameter or keyword argument.
        title=request.title,
        # Provides the `show_creator_name` parameter or keyword argument.
        show_creator_name=request.show_creator_name,
        # Provides the `config` parameter or keyword argument.
        config=config.to_dict(),
        # Provides the `encrypted_secret` parameter or keyword argument.
        encrypted_secret=encrypted.ciphertext,
        # Provides the `secret_nonce` parameter or keyword argument.
        secret_nonce=encrypted.nonce,
        # Provides the `secret_key_version` parameter or keyword argument.
        secret_key_version=encrypted.key_version,
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=utcnow() + timedelta(days=30),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `session.add` with the supplied values.
    session.add(challenge)
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Handles the listed exception so failure remains controlled.
    except DuplicateKeyError:
        # Waits for this asynchronous operation to complete.
        await session.rollback()
        # Checks this condition before executing the nested branch.
        if request.idempotency_key:
            # Computes and stores `concurrent` for subsequent operations.
            concurrent = await session.find_one(
                # Supplies this required nested value.
                FriendChallenge,
                # Supplies this required nested value.
                {
                    # Supplies this literal value to the surrounding declaration or call.
                    "creator_id": principal.user_id,
                    # Supplies this literal value to the surrounding declaration or call.
                    "creation_idempotency_key": request.idempotency_key,
                    # Closes the multiline declaration, call, or collection opened above.
                },
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Checks this condition before executing the nested branch.
            if concurrent:
                # Checks this condition before executing the nested branch.
                if (
                    # Executes this statement as the next step in the surrounding logic.
                    concurrent.creation_request_fingerprint is not None
                    # Executes this statement as the next step in the surrounding logic.
                    and concurrent.creation_request_fingerprint != fingerprint
                    # Begins the nested block or multiline expression completed below.
                ):
                    # Raises this exception to report an invalid or failed operation.
                    raise _idempotency_reused() from None
                # Calls `assert_same_payload` with the supplied values.
                assert_same_payload(concurrent)
                # Returns this result to the caller and ends the current function.
                return concurrent, share_code
        # Executes this statement as the next step in the surrounding logic.
        raise
    # Returns this result to the caller and ends the current function.
    return challenge, share_code


# Defines the `challenge_response` callable and its typed interface.
async def challenge_response(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `challenge` data field.
    challenge: FriendChallenge,
    # Provides the `principal` parameter or keyword argument.
    principal: AuthPrincipal | None = None,
    # Provides the `public_code` parameter or keyword argument.
    public_code: str | None = None,
    # Completes the signature and declares the callable return type.
) -> ChallengeResponse:
    # Computes and stores `creator` for subsequent operations.
    creator = await session.get(Profile, challenge.creator_id)
    # Computes and stores `count` for subsequent operations.
    count = await session.count(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {"friend_challenge_id": challenge.id, "completed_at": {"$ne": None}},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Executes this statement as the next step in the surrounding logic.
    is_owner = principal is not None and principal.user_id == challenge.creator_id
    # Returns this result to the caller and ends the current function.
    return ChallengeResponse(
        # Provides the `id` parameter or keyword argument.
        id=str(challenge.id) if is_owner else None,
        # Provides the `share_code` parameter or keyword argument.
        share_code=public_code or "",
        # Provides the `title` parameter or keyword argument.
        title=challenge.title,
        # Computes and stores `creator_name` for subsequent operations.
        creator_name=(
            # Executes this statement as the next step in the surrounding logic.
            (creator.display_name or "Anonymous breaker")
            # Checks this condition before executing the nested branch.
            if challenge.show_creator_name and creator and creator.deleted_at is None
            # Executes this statement as the next step in the surrounding logic.
            else None
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Provides the `config` parameter or keyword argument.
        config=GameConfigSchema.model_validate(challenge.config),
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=challenge.expires_at,
        # Provides the `revoked` parameter or keyword argument.
        revoked=challenge.revoked_at is not None,
        # Provides the `completed_count` parameter or keyword argument.
        completed_count=count or 0 if is_owner else 0,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `load_challenge` callable and its typed interface.
async def load_challenge(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Supplies this item to the surrounding call or collection.
    share_code: str,
    # Supplies this item to the surrounding call or collection.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> FriendChallenge:
    # Computes and stores `challenge` for subsequent operations.
    challenge = await session.find_one(
        # Supplies this required nested value.
        FriendChallenge,
        {"share_code_hash": identifier_hash(share_code, settings)},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if challenge is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    # Checks this condition before executing the nested branch.
    if challenge.revoked_at or ensure_aware(challenge.expires_at) <= utcnow():
        # Capability-token lookups deliberately do not distinguish absent,
        # expired, and revoked records.
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "CHALLENGE_NOT_FOUND", "Challenge not found.")
    # Returns this result to the caller and ends the current function.
    return challenge


# Defines the `start_challenge` callable and its typed interface.
async def start_challenge(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `challenge` data field.
    challenge: FriendChallenge,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `practice` parameter or keyword argument.
    practice: bool = False,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `existing` for subsequent operations.
    existing = await session.find_one(
        # Supplies this required nested value.
        GameSession,
        # Supplies this required nested value.
        {"owner_id": principal.user_id, "friend_challenge_id": challenge.id},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if existing is not None and expire_game_record(existing, now=utcnow()):
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Checks this condition before executing the nested branch.
    if existing and (existing.status == GameStatus.ACTIVE.value or not practice):
        # Returns this result to the caller and ends the current function.
        return existing
    # Computes and stores `config` for subsequent operations.
    config = GameConfig.from_dict(challenge.config)
    # Computes and stores `secret_code` for subsequent operations.
    secret_code = cipher.decrypt(
        # Supplies this item to the surrounding call or collection.
        challenge.encrypted_secret,
        # Supplies this item to the surrounding call or collection.
        challenge.secret_nonce,
        # Supplies this item to the surrounding call or collection.
        challenge.secret_key_version,
        # Provides the `context` parameter or keyword argument.
        context=f"challenge:{challenge.share_code_hash}:{RULE_SET_VERSION}",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `request` for subsequent operations.
    request = CreateGameRequest(
        # Provides the `mode` parameter or keyword argument.
        mode=GameMode.PRACTICE if practice else GameMode.FRIEND_CHALLENGE,
        # Provides the `config` parameter or keyword argument.
        config=GameConfigSchema.model_validate(config.to_dict()),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return await create_game(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        request,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `secret_override` parameter or keyword argument.
        secret_override=secret_code,
        # Provides the `friend_id` parameter or keyword argument.
        friend_id=None if practice else challenge.id,
        # Provides the `linked_expires_at` parameter or keyword argument.
        linked_expires_at=None if practice else challenge.expires_at,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `create_room` callable and its typed interface.
async def create_room(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `difficulty` data field.
    difficulty: str,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Provides the `idempotency_key` parameter or keyword argument.
    idempotency_key: str | None = None,
    # Completes the signature and declares the callable return type.
) -> tuple[MultiplayerRoom, str]:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `fingerprint` for subsequent operations.
    fingerprint = (
        # Calls `creation_request_fingerprint` with the supplied values.
        creation_request_fingerprint("room.create", {"difficulty": difficulty}, settings)
        # Checks this condition before executing the nested branch.
        if idempotency_key
        # Executes this statement as the next step in the surrounding logic.
        else None
        # Closes the multiline call, declaration, or collection started above.
    )
    # Checks this condition before executing the nested branch.
    if idempotency_key:
        # Computes and stores `room_code` for subsequent operations.
        room_code = idempotent_invite_code("room", principal.user_id, idempotency_key, settings)
        # Computes and stores `existing` for subsequent operations.
        existing = await session.find_one(
            # Supplies this required nested value.
            MultiplayerRoom,
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "owner_id": principal.user_id,
                # Supplies this literal value to the surrounding declaration or call.
                "creation_idempotency_key": idempotency_key,
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Checks this condition before executing the nested branch.
        if existing:
            # Checks this condition before executing the nested branch.
            if (
                # Executes this statement as the next step in the surrounding logic.
                existing.creation_request_fingerprint is not None
                # Executes this statement as the next step in the surrounding logic.
                and existing.creation_request_fingerprint != fingerprint
                # Begins the nested block or multiline expression completed below.
            ):
                # Raises this exception to report an invalid or failed operation.
                raise _idempotency_reused()
            # Checks this condition before executing the nested branch.
            if existing.config != get_preset(difficulty).to_dict():
                # Raises this exception to report an invalid or failed operation.
                raise _idempotency_reused()
            # Returns this result to the caller and ends the current function.
            return existing, room_code
    # Computes and stores `config` for subsequent operations.
    config = get_preset(difficulty)
    # Computes and stores `secret_code` for subsequent operations.
    secret_code = generate_secret(config)
    # Computes and stores `room_code` for subsequent operations.
    room_code = (
        # Calls `idempotent_invite_code` with the supplied values.
        idempotent_invite_code("room", principal.user_id, idempotency_key, settings)
        # Checks this condition before executing the nested branch.
        if idempotency_key
        # Executes this statement as the next step in the surrounding logic.
        else public_token(16)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `room_id` for subsequent operations.
    room_id = uuid.uuid4()
    # Computes and stores `context` for subsequent operations.
    context = f"room:{room_id}:{RULE_SET_VERSION}"
    # Computes and stores `encrypted` for subsequent operations.
    encrypted = cipher.encrypt(secret_code, context=context)
    # Computes and stores `room` for subsequent operations.
    room = MultiplayerRoom(
        # Provides the `id` parameter or keyword argument.
        id=room_id,
        # Provides the `room_code_hash` parameter or keyword argument.
        room_code_hash=identifier_hash(room_code, settings),
        # Provides the `creation_idempotency_key` parameter or keyword argument.
        creation_idempotency_key=idempotency_key,
        # Provides the `creation_request_fingerprint` parameter or keyword argument.
        creation_request_fingerprint=fingerprint,
        # Provides the `owner_id` parameter or keyword argument.
        owner_id=principal.user_id,
        # Provides the `config` parameter or keyword argument.
        config=config.to_dict(),
        # Provides the `encrypted_secret` parameter or keyword argument.
        encrypted_secret=encrypted.ciphertext,
        # Provides the `secret_nonce` parameter or keyword argument.
        secret_nonce=encrypted.nonce,
        # Provides the `secret_key_version` parameter or keyword argument.
        secret_key_version=encrypted.key_version,
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=utcnow() + timedelta(hours=2),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `session.add` with the supplied values.
    session.add(room)
    # Starts a protected operation whose expected failures are handled below.
    try:
        # The models intentionally use identifiers instead of a write-side ORM
        # Persist the room before its first membership so later lookups never see
        # a membership without its owning room.
        # Waits for this asynchronous operation to complete.
        await session.flush()
        # Calls `session.add` with the supplied values.
        session.add(MultiplayerMember(room_id=room.id, user_id=principal.user_id))
        # Waits for this asynchronous operation to complete.
        await session.flush()
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Handles the listed exception so failure remains controlled.
    except DuplicateKeyError:
        # Waits for this asynchronous operation to complete.
        await session.rollback()
        # Checks this condition before executing the nested branch.
        if idempotency_key:
            # Computes and stores `concurrent` for subsequent operations.
            concurrent = await session.find_one(
                # Supplies this required nested value.
                MultiplayerRoom,
                # Supplies this required nested value.
                {
                    # Supplies this literal value to the surrounding declaration or call.
                    "owner_id": principal.user_id,
                    # Supplies this literal value to the surrounding declaration or call.
                    "creation_idempotency_key": idempotency_key,
                    # Closes the multiline declaration, call, or collection opened above.
                },
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Checks this condition before executing the nested branch.
            if concurrent:
                # Checks this condition before executing the nested branch.
                if (
                    # Executes this statement as the next step in the surrounding logic.
                    concurrent.creation_request_fingerprint is not None
                    # Executes this statement as the next step in the surrounding logic.
                    and concurrent.creation_request_fingerprint != fingerprint
                    # Begins the nested block or multiline expression completed below.
                ):
                    # Raises this exception to report an invalid or failed operation.
                    raise _idempotency_reused() from None
                # Checks this condition before executing the nested branch.
                if concurrent.config != config.to_dict():
                    # Raises this exception to report an invalid or failed operation.
                    raise _idempotency_reused() from None
                # Returns this result to the caller and ends the current function.
                return concurrent, room_code
        # Executes this statement as the next step in the surrounding logic.
        raise
    # Returns this result to the caller and ends the current function.
    return room, room_code


# Defines the `_create_room_game` callable and its typed interface.
async def _create_room_game(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Declares the typed `config` data field.
    config: GameConfig,
    # Declares the typed `secret_code` data field.
    secret_code: tuple[str, ...],
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Completes the signature and declares the callable return type.
) -> GameSession:
    # Computes and stores `request` for subsequent operations.
    request = CreateGameRequest(
        # Provides the `mode` parameter or keyword argument.
        mode=GameMode.DUEL,
        # Provides the `difficulty` parameter or keyword argument.
        difficulty=preset_name(config) or "normal",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return await create_game(
        # Supplies this item to the surrounding call or collection.
        session,
        # Supplies this item to the surrounding call or collection.
        principal,
        # Supplies this item to the surrounding call or collection.
        request,
        # Supplies this item to the surrounding call or collection.
        cipher,
        # Provides the `secret_override` parameter or keyword argument.
        secret_override=secret_code,
        # Provides the `room_id` parameter or keyword argument.
        room_id=room.id,
        # Provides the `linked_expires_at` parameter or keyword argument.
        linked_expires_at=room.expires_at,
        # Provides the `commit` parameter or keyword argument.
        commit=False,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `join_room` callable and its typed interface.
async def join_room(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `room_code` data field.
    room_code: str,
    # Declares the typed `_cipher` data field.
    _cipher: SecretCipher,
    # Declares the typed `settings` data field.
    settings: Settings,
    # Completes the signature and declares the callable return type.
) -> MultiplayerRoom:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Computes and stores `room` for subsequent operations.
    room = await session.find_one(
        # Supplies this required nested value.
        MultiplayerRoom,
        {"room_code_hash": identifier_hash(room_code, settings)},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if room is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found.")
    # Checks this condition before executing the nested branch.
    if ensure_aware(room.expires_at) <= utcnow():
        # Raises this exception to report an invalid or failed operation.
        raise APIError(410, "ROOM_EXPIRED", "This room has expired.")
    # Computes and stores `member` for subsequent operations.
    member = await session.find_one(
        # Supplies this required nested value.
        MultiplayerMember,
        {"room_id": room.id, "user_id": principal.user_id},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Computes and stores `members_count` for subsequent operations.
    members_count = await session.count(MultiplayerMember, {"room_id": room.id})
    # Checks this condition before executing the nested branch.
    if member is None:
        # Checks this condition before executing the nested branch.
        if (members_count or 0) >= 2:
            # Raises this exception to report an invalid or failed operation.
            raise APIError(409, "ROOM_FULL", "This room already has two players.")
        # Checks this condition before executing the nested branch.
        if room.status != "waiting":
            # Raises this exception to report an invalid or failed operation.
            raise APIError(409, "ROOM_NOT_JOINABLE", "This room is no longer accepting players.")
        # Calls `session.add` with the supplied values.
        session.add(MultiplayerMember(room_id=room.id, user_id=principal.user_id))
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return room


# Defines the `ready_room` callable and its typed interface.
async def ready_room(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `cipher` data field.
    cipher: SecretCipher,
    # Completes the signature and declares the callable return type.
) -> tuple[MultiplayerRoom, list[dict[str, object]]]:
    # Documents the purpose or contract of this module, class, or function.
    """Mark a room member ready and atomically start a full two-player room."""

    # Computes and stores `room` for subsequent operations.
    room = await load_room_for_member(session, room_id, principal, for_update=True)
    # Checks this condition before executing the nested branch.
    if room.status == "expired":
        # Waits for this asynchronous operation to complete.
        await session.commit()
        # Raises this exception to report an invalid or failed operation.
        raise APIError(410, "ROOM_EXPIRED", "This room has expired.")
    # Computes and stores `member` for subsequent operations.
    member = await session.find_one(
        # Supplies this required nested value.
        MultiplayerMember,
        {"room_id": room.id, "user_id": principal.user_id},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Checks this condition before executing the nested branch.
    if member is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found or you are not a member.")
    # Checks this condition before executing the nested branch.
    if room.status != "waiting":
        # Checks this condition before executing the nested branch.
        if member.ready:
            # Waits for this asynchronous operation to complete.
            await session.commit()
            # Returns this result to the caller and ends the current function.
            return room, []
        # Raises this exception to report an invalid or failed operation.
        raise APIError(409, "ROOM_ALREADY_STARTED", "This room has already started.")

    # Computes and stores `events` for subsequent operations.
    events: list[dict[str, object]] = []
    # Checks this condition before executing the nested branch.
    if not member.ready:
        # Computes and stores `member.ready` for subsequent operations.
        member.ready = True
        # Computes and stores `member.ready_at` for subsequent operations.
        member.ready_at = utcnow()
        # Calls `events.append` with the supplied values.
        events.append(
            # Waits for this asynchronous operation to complete.
            await record_room_event(
                # Supplies this item to the surrounding call or collection.
                session,
                # Supplies this item to the surrounding call or collection.
                room,
                # Supplies this item to the surrounding call or collection.
                "member_ready",
                # Begins the nested block or multiline expression completed below.
                {
                    # Associates the `userId` key with its value.
                    "userId": str(principal.user_id),
                    # Associates the `ready` key with its value.
                    "ready": True,
                    # Associates the `readyAt` key with its value.
                    "readyAt": member.ready_at.isoformat(),
                    # Closes the multiline call, declaration, or collection started above.
                },
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )

    # Computes and stores `member_rows` for subsequent operations.
    room_members = await session.find_many(
        # Supplies this required nested value.
        MultiplayerMember,
        # Supplies this required nested value.
        {"room_id": room.id},
        # Stores `sort` because later steps depend on this value.
        sort=[("joined_at", 1), ("_id", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `member_rows` because later steps depend on this value.
    member_rows = [
        # Supplies this required nested value.
        (room_member, profile)
        # Iterates over these values so each item receives the same processing.
        for room_member in room_members
        # Guards the nested operation so it runs only when this condition is satisfied.
        if (profile := await session.get(Profile, room_member.user_id)) is not None
        # Closes the multiline declaration, call, or collection opened above.
    ]
    # Checks this condition before executing the nested branch.
    if len(member_rows) == 2 and all(room_member.ready for room_member, _ in member_rows):
        # Computes and stores `config` for subsequent operations.
        config = GameConfig.from_dict(room.config)
        # Computes and stores `secret_code` for subsequent operations.
        secret_code = cipher.decrypt(
            # Supplies this item to the surrounding call or collection.
            room.encrypted_secret,
            # Supplies this item to the surrounding call or collection.
            room.secret_nonce,
            # Supplies this item to the surrounding call or collection.
            room.secret_key_version,
            # Provides the `context` parameter or keyword argument.
            context=f"room:{room.id}:{RULE_SET_VERSION}",
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `existing_owner_ids` for subsequent operations.
        existing_games = await session.find_many(GameSession, {"room_id": room.id})
        # Stores `existing_owner_ids` because later steps depend on this value.
        existing_owner_ids = {game.owner_id for game in existing_games}
        # Computes and stores `duel_started_at` for subsequent operations.
        duel_started_at = utcnow()
        # Iterates through the supplied values for the nested operation.
        for room_member, profile in member_rows:
            # Checks this condition before executing the nested branch.
            if room_member.user_id in existing_owner_ids:
                # Skips the remaining work and advances to the next iteration.
                continue
            # Computes and stores `room_principal` for subsequent operations.
            room_principal = AuthPrincipal(
                # Provides the `user_id` parameter or keyword argument.
                user_id=room_member.user_id,
                # Provides the `is_anonymous` parameter or keyword argument.
                is_anonymous=profile.is_anonymous,
                # Provides the `session_id` parameter or keyword argument.
                session_id=None,
                # Provides the `issued_at` parameter or keyword argument.
                issued_at=duel_started_at,
                # Provides the `authenticated_at` parameter or keyword argument.
                authenticated_at=None,
                # Provides the `assurance_level` parameter or keyword argument.
                assurance_level=None,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Computes and stores `game` for subsequent operations.
            game = await _create_room_game(
                # Executes this statement as the next step in the surrounding logic.
                session,
                # Supplies this item to the surrounding call or collection.
                room_principal,
                # Supplies this item to the surrounding call or collection.
                room,
                # Supplies this item to the surrounding call or collection.
                config,
                # Supplies this item to the surrounding call or collection.
                secret_code,
                # Supplies this item to the surrounding call or collection.
                cipher,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Computes and stores `game.started_at` for subsequent operations.
            game.started_at = duel_started_at
        # Iterates over these values so each item receives the same processing.
        for game in existing_games:
            # Stores `game.started_at` because later steps depend on this value.
            game.started_at = duel_started_at
        # Computes and stores `room.status` for subsequent operations.
        room.status = "active"
        # Calls `events.append` with the supplied values.
        events.append(
            # Waits for this asynchronous operation to complete.
            await record_room_event(
                # Supplies this item to the surrounding call or collection.
                session,
                # Supplies this item to the surrounding call or collection.
                room,
                # Supplies this item to the surrounding call or collection.
                "room_started",
                # Supplies this item to the surrounding call or collection.
                {"startedAt": duel_started_at.isoformat()},
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Waits for this asynchronous operation to complete.
    await session.commit()
    # Returns this result to the caller and ends the current function.
    return room, events


# Defines the `load_room_for_member` callable and its typed interface.
async def load_room_for_member(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `room_id` data field.
    room_id: uuid.UUID,
    # Declares the typed `principal` data field.
    principal: AuthPrincipal,
    # Makes the following parameters keyword-only for clear call sites.
    *,
    # Provides the `for_update` parameter or keyword argument.
    for_update: bool = False,
    # Completes the signature and declares the callable return type.
) -> MultiplayerRoom:
    # Waits for this asynchronous operation to complete.
    await ensure_profile(session, principal)
    # Stores `member` because later steps depend on this value.
    member = await session.find_one(
        # Supplies this required nested value.
        MultiplayerMember,
        {"room_id": room_id, "user_id": principal.user_id},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `room` because later steps depend on this value.
    room = await session.get(MultiplayerRoom, room_id) if member is not None else None
    # Checks this condition before executing the nested branch.
    if room is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "ROOM_NOT_FOUND", "Room not found or you are not a member.")
    # Checks this condition before executing the nested branch.
    if ensure_aware(room.expires_at) <= utcnow():
        # Computes and stores `room.status` for subsequent operations.
        room.status = "expired"
    # Stores `games` because later steps depend on this value.
    games = await session.find_many(GameSession, {"room_id": room.id}, sort=[("_id", 1)])
    # Checks this condition before executing the nested branch.
    if (
        # Executes this statement as the next step in the surrounding logic.
        for_update
        # Executes this statement as the next step in the surrounding logic.
        and room.status == "active"
        # Executes this statement as the next step in the surrounding logic.
        and len(games) == 2
        # Executes this statement as the next step in the surrounding logic.
        and all(GameStatus(game.status).terminal for game in games)
        # Begins the nested block or multiline expression completed below.
    ):
        # Computes and stores `won_games` for subsequent operations.
        won_games = sorted(
            # Supplies this item to the surrounding call or collection.
            (game for game in games if game.status == GameStatus.WON.value),
            # Provides the `key` parameter or keyword argument.
            key=lambda game: ensure_aware(game.completed_at or utcnow()),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `room.status` for subsequent operations.
        room.status = "completed"
        # Checks this condition before executing the nested branch.
        if not won_games:
            # Computes and stores `room.winner_id` for subsequent operations.
            room.winner_id = None
            # Computes and stores `room.winner_at` for subsequent operations.
            room.winner_at = None
            # Computes and stores `room.is_tie` for subsequent operations.
            room.is_tie = True
        # Checks this alternative when previous conditions were false.
        elif len(won_games) == 2:
            # Computes and stores `first_at` for subsequent operations.
            first_at = ensure_aware(won_games[0].completed_at or utcnow())
            # Computes and stores `second_at` for subsequent operations.
            second_at = ensure_aware(won_games[1].completed_at or utcnow())
            # Computes and stores `room.is_tie` for subsequent operations.
            room.is_tie = (second_at - first_at).total_seconds() * 1000 <= (
                # Calls `get_settings` with the supplied values.
                get_settings().room_tie_window_ms
                # Closes the multiline call, declaration, or collection started above.
            )
            # Checks this condition before executing the nested branch.
            if room.is_tie:
                # Computes and stores `room.winner_id` for subsequent operations.
                room.winner_id = None
                # Computes and stores `room.winner_at` for subsequent operations.
                room.winner_at = first_at
            # Handles the remaining case not matched by earlier branches.
            else:
                # Computes and stores `room.winner_id` for subsequent operations.
                room.winner_id = won_games[0].owner_id
                # Computes and stores `room.winner_at` for subsequent operations.
                room.winner_at = first_at
        # Handles the remaining case not matched by earlier branches.
        else:
            # Computes and stores `room.winner_id` for subsequent operations.
            room.winner_id = won_games[0].owner_id
            # Computes and stores `room.winner_at` for subsequent operations.
            room.winner_at = won_games[0].completed_at
            # Computes and stores `room.is_tie` for subsequent operations.
            room.is_tie = False
    # Returns this result to the caller and ends the current function.
    return room


# Defines the `room_response` callable and its typed interface.
async def room_response(
    # Declares the typed `session` data field.
    session: MongoSession,
    # Declares the typed `room` data field.
    room: MultiplayerRoom,
    # Provides the `room_code` parameter or keyword argument.
    room_code: str | None = None,
    # Provides the `viewer_id` parameter or keyword argument.
    viewer_id: uuid.UUID | None = None,
    # Completes the signature and declares the callable return type.
) -> RoomResponse:
    # Stores `room_members` because later steps depend on this value.
    room_members = await session.find_many(
        # Supplies this required nested value.
        MultiplayerMember,
        {"room_id": room.id},
        sort=[("joined_at", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `room_games` because later steps depend on this value.
    room_games = await session.find_many(GameSession, {"room_id": room.id})
    # Stores `games_by_owner` because later steps depend on this value.
    games_by_owner = {game.owner_id: game for game in room_games}
    # Stores `rows` because later steps depend on this value.
    rows = [
        # Supplies this required nested value.
        (member, profile, games_by_owner.get(member.user_id))
        # Iterates over these values so each item receives the same processing.
        for member in room_members
        # Guards the nested operation so it runs only when this condition is satisfied.
        if (profile := await session.get(Profile, member.user_id)) is not None
        # Closes the multiline declaration, call, or collection opened above.
    ]
    # Computes and stores `members` for subsequent operations.
    members = [
        # Calls `RoomMemberResponse` with the supplied values.
        RoomMemberResponse(
            # Provides the `user_id` parameter or keyword argument.
            user_id=member.user_id,
            # Provides the `display_name` parameter or keyword argument.
            display_name=profile.display_name or "Anonymous breaker",
            # Provides the `connected` parameter or keyword argument.
            connected=member.connected,
            # Provides the `ready` parameter or keyword argument.
            ready=member.ready,
            # Provides the `ready_at` parameter or keyword argument.
            ready_at=member.ready_at,
            # Provides the `attempts_used` parameter or keyword argument.
            attempts_used=game.attempts_used if game else 0,
            # Provides the `completed` parameter or keyword argument.
            completed=bool(game and GameStatus(game.status).terminal),
            # Provides the `game_id` parameter or keyword argument.
            game_id=(game.public_id if game is not None and member.user_id == viewer_id else None),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Iterates through the supplied values for the nested operation.
        for member, profile, game in rows
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Returns this result to the caller and ends the current function.
    return RoomResponse(
        # Provides the `id` parameter or keyword argument.
        id=room.id,
        # Provides the `room_code` parameter or keyword argument.
        room_code=room_code,
        # Provides the `status` parameter or keyword argument.
        status=room.status,
        # Provides the `config` parameter or keyword argument.
        config=GameConfigSchema.model_validate(room.config),
        # Provides the `members` parameter or keyword argument.
        members=members,
        # Provides the `winner_id` parameter or keyword argument.
        winner_id=room.winner_id,
        # Provides the `is_tie` parameter or keyword argument.
        is_tie=room.is_tie,
        # Provides the `expires_at` parameter or keyword argument.
        expires_at=room.expires_at,
        # Provides the `event_sequence` parameter or keyword argument.
        event_sequence=room.event_sequence,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `profile_response` callable and its typed interface.
async def profile_response(session: MongoSession, principal: AuthPrincipal) -> ProfileResponse:
    # Computes and stores `profile` for subsequent operations.
    profile = await ensure_profile(session, principal)
    # Waits for this asynchronous operation to complete.
    await session.commit()
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


# Defines the `normalize_display_name` callable and its typed interface.
def normalize_display_name(value: str) -> str:
    # Returns this result to the caller and ends the current function.
    return unicodedata.normalize("NFKC", value).casefold()


# Defines the `csv_safe` callable and its typed interface.
def csv_safe(value: object) -> str:
    # Computes and stores `text` for subsequent operations.
    text = str(value)
    # Returns this result to the caller and ends the current function.
    return f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


# Defines the `export_user_csv` callable and its typed interface.
async def export_user_csv(session: MongoSession, principal: AuthPrincipal) -> str:
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, principal.user_id)
    # Computes and stores `player_name` for subsequent operations.
    player_name = profile.display_name if profile and profile.display_name else "Anonymous breaker"
    # Computes and stores `games` for subsequent operations.
    games = await session.find_many(
        # Supplies this required nested value.
        GameSession,
        {"owner_id": principal.user_id},
        sort=[("created_at", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Computes and stores `output` for subsequent operations.
    output = io.StringIO(newline="")
    # Computes and stores `writer` for subsequent operations.
    writer = csv.writer(output)
    # Calls `writer.writerow` with the supplied values.
    writer.writerow(
        # Begins the nested block or multiline expression completed below.
        [
            # Supplies this item to the surrounding call or collection.
            "timestamp",
            # Supplies this item to the surrounding call or collection.
            "player_name",
            # Supplies this item to the surrounding call or collection.
            "mode",
            # Supplies this item to the surrounding call or collection.
            "difficulty",
            # Supplies this item to the surrounding call or collection.
            "code_maker",
            # Supplies this item to the surrounding call or collection.
            "number_of_colours",
            # Supplies this item to the surrounding call or collection.
            "code_length",
            # Supplies this item to the surrounding call or collection.
            "duplicates_allowed",
            # Supplies this item to the surrounding call or collection.
            "attempts_used",
            # Supplies this item to the surrounding call or collection.
            "maximum_attempts",
            # Supplies this item to the surrounding call or collection.
            "score",
            # Supplies this item to the surrounding call or collection.
            "scoring_version",
            # Supplies this item to the surrounding call or collection.
            "result",
            # Closes the multiline call, declaration, or collection started above.
        ]
        # Closes the multiline call, declaration, or collection started above.
    )
    # Iterates through the supplied values for the nested operation.
    for game in games:
        # Computes and stores `config` for subsequent operations.
        config = GameConfig.from_dict(game.config)
        # Calls `writer.writerow` with the supplied values.
        writer.writerow(
            # Begins the nested block or multiline expression completed below.
            [
                # Calls `ensure_aware` with the supplied values.
                ensure_aware(game.created_at).isoformat(),
                # Calls `csv_safe` with the supplied values.
                csv_safe(player_name),
                # Calls `csv_safe` with the supplied values.
                csv_safe(game.mode),
                # Calls `csv_safe` with the supplied values.
                csv_safe(game.difficulty or "custom"),
                # Supplies this item to the surrounding call or collection.
                config.code_maker.value,
                # Calls `len` with the supplied values.
                len(config.colours),
                # Supplies this item to the surrounding call or collection.
                config.code_length,
                # Calls `str` with the supplied values.
                str(config.duplicates_allowed).lower(),
                # Supplies this item to the surrounding call or collection.
                game.attempts_used,
                # Supplies this item to the surrounding call or collection.
                game.maximum_attempts,
                # Supplies this item to the surrounding call or collection.
                game.final_score or 0,
                # Supplies this item to the surrounding call or collection.
                game.scoring_version,
                # Supplies this item to the surrounding call or collection.
                game.status,
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Closes the multiline call, declaration, or collection started above.
        )
    # Returns this result to the caller and ends the current function.
    return output.getvalue()


# Defines the `_csv_document` callable and its typed interface.
def _csv_document(header: list[str], rows: list[list[object]]) -> str:
    # Computes and stores `output` for subsequent operations.
    output = io.StringIO(newline="")
    # Computes and stores `writer` for subsequent operations.
    writer = csv.writer(output)
    # Calls `writer.writerow` with the supplied values.
    writer.writerow(header)
    # Calls `writer.writerows` with the supplied values.
    writer.writerows([[csv_safe(value) for value in row] for row in rows])
    # Returns this result to the caller and ends the current function.
    return output.getvalue()


# Defines the `export_user_archive` callable and its typed interface.
async def export_user_archive(session: MongoSession, principal: AuthPrincipal) -> bytes:
    # Documents the purpose or contract of this module, class, or function.
    """Build a complete, secret-free, portable account export."""
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, principal.user_id)
    # Checks this condition before executing the nested branch.
    if profile is None:
        # Raises this exception to report an invalid or failed operation.
        raise APIError(404, "PROFILE_NOT_FOUND", "Profile not found.")
    # Computes and stores `games` for subsequent operations.
    games = await session.find_many(
        # Supplies this required nested value.
        GameSession,
        {"owner_id": principal.user_id},
        sort=[("created_at", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Computes and stores `achievements` for subsequent operations.
    achievement_documents = await session.find_many(
        # Supplies this required nested value.
        UserAchievement,
        {"user_id": principal.user_id},
        sort=[("awarded_at", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `achievements` because later steps depend on this value.
    achievements = [
        # Supplies this required nested value.
        (item.achievement_key, item.awarded_at, item.game_id)
        # Iterates over these values so each item receives the same processing.
        for item in achievement_documents
        # Closes the multiline declaration, call, or collection opened above.
    ]
    # Computes and stores `challenges` for subsequent operations.
    challenges = await session.find_many(
        # Supplies this required nested value.
        FriendChallenge,
        {"creator_id": principal.user_id},
        sort=[("created_at", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Computes and stores `memberships` for subsequent operations.
    membership_documents = await session.find_many(
        # Supplies this required nested value.
        MultiplayerMember,
        {"user_id": principal.user_id},
        sort=[("joined_at", 1)],
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `memberships` because later steps depend on this value.
    memberships = [
        # Supplies this required nested value.
        (member, room)
        # Iterates over these values so each item receives the same processing.
        for member in membership_documents
        # Guards the nested operation so it runs only when this condition is satisfied.
        if (room := await session.get(MultiplayerRoom, member.room_id)) is not None
        # Closes the multiline declaration, call, or collection opened above.
    ]

    # Computes and stores `profile_document` for subsequent operations.
    profile_document = {
        # Associates the `id` key with its value.
        "id": str(profile.id),
        # Associates the `displayName` key with its value.
        "displayName": profile.display_name,
        # Associates the `isAnonymous` key with its value.
        "isAnonymous": profile.is_anonymous,
        # Associates the `publicLeaderboards` key with its value.
        "publicLeaderboards": profile.public_leaderboards,
        # Associates the `createdAt` key with its value.
        "createdAt": ensure_aware(profile.created_at).isoformat(),
        # Associates the `exportedAt` key with its value.
        "exportedAt": utcnow().isoformat(),
        # Closes the multiline call, declaration, or collection started above.
    }
    # Computes and stores `game_rows` for subsequent operations.
    game_rows: list[list[object]] = []
    # Computes and stores `attempt_rows` for subsequent operations.
    attempt_rows: list[list[object]] = []
    # Iterates through the supplied values for the nested operation.
    for game in games:
        # Calls `game_rows.append` with the supplied values.
        game_rows.append(
            # Begins the nested block or multiline expression completed below.
            [
                # Supplies this item to the surrounding call or collection.
                game.public_id,
                # Calls `ensure_aware` with the supplied values.
                ensure_aware(game.created_at).isoformat(),
                # Supplies this item to the surrounding call or collection.
                game.mode,
                # Supplies this item to the surrounding call or collection.
                game.difficulty or "custom",
                # Calls `json.dumps` with the supplied values.
                json.dumps(game.config, ensure_ascii=False, sort_keys=True),
                # Supplies this item to the surrounding call or collection.
                game.status,
                # Supplies this item to the surrounding call or collection.
                game.attempts_used,
                # Supplies this item to the surrounding call or collection.
                game.maximum_attempts,
                # Supplies this item to the surrounding call or collection.
                game.final_score or 0,
                # Supplies this item to the surrounding call or collection.
                game.scoring_version,
                # Supplies this item to the surrounding call or collection.
                game.ranked_eligibility,
                # Calls `ensure_aware` with the supplied values.
                ensure_aware(game.completed_at).isoformat() if game.completed_at else "",
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `attempt_rows.extend` with the supplied values.
        attempt_rows.extend(
            # Begins the nested block or multiline expression completed below.
            [
                # Supplies this item to the surrounding call or collection.
                game.public_id,
                # Supplies this item to the surrounding call or collection.
                attempt.attempt_number,
                # Calls `json.dumps` with the supplied values.
                json.dumps(attempt.guess, ensure_ascii=False),
                # Supplies this item to the surrounding call or collection.
                attempt.black_pegs,
                # Supplies this item to the surrounding call or collection.
                attempt.white_pegs,
                # Calls `ensure_aware` with the supplied values.
                ensure_aware(attempt.submitted_at).isoformat(),
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Iterates through the supplied values for the nested operation.
            for attempt in game.attempts
            # Closes the multiline call, declaration, or collection started above.
        )

    # Computes and stores `archive` for subsequent operations.
    archive = io.BytesIO()
    # Acquires this managed resource and guarantees cleanup afterward.
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        # Calls `output.writestr` with the supplied values.
        output.writestr(
            # Supplies this item to the surrounding call or collection.
            "manifest.json",
            # Calls `json.dumps` with the supplied values.
            json.dumps(
                # Begins the nested block or multiline expression completed below.
                {
                    # Associates the `formatVersion` key with its value.
                    "formatVersion": 1,
                    # Associates the `files` key with its value.
                    "files": [
                        # Supplies this item to the surrounding call or collection.
                        "profile.json",
                        # Supplies this item to the surrounding call or collection.
                        "games.csv",
                        # Supplies this item to the surrounding call or collection.
                        "attempts.csv",
                        # Supplies this item to the surrounding call or collection.
                        "achievements.csv",
                        # Supplies this item to the surrounding call or collection.
                        "challenges.csv",
                        # Supplies this item to the surrounding call or collection.
                        "rooms.csv",
                        # Closes the multiline call, declaration, or collection started above.
                    ],
                    # Associates the `excluded` key with its value.
                    "excluded": [
                        # Supplies this item to the surrounding call or collection.
                        "authentication credentials",
                        # Supplies this item to the surrounding call or collection.
                        "active and historical secret codes",
                        # Supplies this item to the surrounding call or collection.
                        "invite tokens",
                        # Supplies this item to the surrounding call or collection.
                        "encryption material",
                        # Closes the multiline call, declaration, or collection started above.
                    ],
                    # Closes the multiline call, declaration, or collection started above.
                },
                # Provides the `ensure_ascii` parameter or keyword argument.
                ensure_ascii=False,
                # Provides the `indent` parameter or keyword argument.
                indent=2,
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `output.writestr` with the supplied values.
        output.writestr("profile.json", json.dumps(profile_document, ensure_ascii=False, indent=2))
        # Calls `output.writestr` with the supplied values.
        output.writestr(
            # Supplies this item to the surrounding call or collection.
            "games.csv",
            # Calls `_csv_document` with the supplied values.
            _csv_document(
                # Begins the nested block or multiline expression completed below.
                [
                    # Supplies this item to the surrounding call or collection.
                    "game_id",
                    # Supplies this item to the surrounding call or collection.
                    "created_at",
                    # Supplies this item to the surrounding call or collection.
                    "mode",
                    # Supplies this item to the surrounding call or collection.
                    "difficulty",
                    # Supplies this item to the surrounding call or collection.
                    "config",
                    # Supplies this item to the surrounding call or collection.
                    "result",
                    # Supplies this item to the surrounding call or collection.
                    "attempts_used",
                    # Supplies this item to the surrounding call or collection.
                    "maximum_attempts",
                    # Supplies this item to the surrounding call or collection.
                    "score",
                    # Supplies this item to the surrounding call or collection.
                    "scoring_version",
                    # Supplies this item to the surrounding call or collection.
                    "ranking_eligibility",
                    # Supplies this item to the surrounding call or collection.
                    "completed_at",
                    # Closes the multiline call, declaration, or collection started above.
                ],
                # Supplies this item to the surrounding call or collection.
                game_rows,
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `output.writestr` with the supplied values.
        output.writestr(
            # Supplies this item to the surrounding call or collection.
            "attempts.csv",
            # Calls `_csv_document` with the supplied values.
            _csv_document(
                # Begins the nested block or multiline expression completed below.
                [
                    # Supplies this item to the surrounding call or collection.
                    "game_id",
                    # Supplies this item to the surrounding call or collection.
                    "attempt_number",
                    # Supplies this item to the surrounding call or collection.
                    "guess",
                    # Supplies this item to the surrounding call or collection.
                    "black_pegs",
                    # Supplies this item to the surrounding call or collection.
                    "white_pegs",
                    # Supplies this item to the surrounding call or collection.
                    "submitted_at",
                    # Closes the multiline call, declaration, or collection started above.
                ],
                # Supplies this item to the surrounding call or collection.
                attempt_rows,
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `output.writestr` with the supplied values.
        output.writestr(
            # Supplies this item to the surrounding call or collection.
            "achievements.csv",
            # Calls `_csv_document` with the supplied values.
            _csv_document(
                # Supplies this item to the surrounding call or collection.
                ["achievement_key", "awarded_at", "game_id"],
                # Begins the nested block or multiline expression completed below.
                [
                    # Executes this statement as the next step in the surrounding logic.
                    [key, ensure_aware(awarded_at).isoformat(), game_id or ""]
                    # Iterates through the supplied values for the nested operation.
                    for key, awarded_at, game_id in achievements
                    # Closes the multiline call, declaration, or collection started above.
                ],
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `output.writestr` with the supplied values.
        output.writestr(
            # Supplies this item to the surrounding call or collection.
            "challenges.csv",
            # Calls `_csv_document` with the supplied values.
            _csv_document(
                # Begins the nested block or multiline expression completed below.
                [
                    # Supplies this item to the surrounding call or collection.
                    "challenge_id",
                    # Supplies this item to the surrounding call or collection.
                    "title",
                    # Supplies this item to the surrounding call or collection.
                    "show_creator_name",
                    # Supplies this item to the surrounding call or collection.
                    "config",
                    # Supplies this item to the surrounding call or collection.
                    "created_at",
                    # Supplies this item to the surrounding call or collection.
                    "expires_at",
                    # Supplies this item to the surrounding call or collection.
                    "revoked_at",
                    # Closes the multiline call, declaration, or collection started above.
                ],
                # Begins the nested block or multiline expression completed below.
                [
                    # Begins the nested block or multiline expression completed below.
                    [
                        # Supplies this item to the surrounding call or collection.
                        challenge.id,
                        # Supplies this item to the surrounding call or collection.
                        challenge.title or "",
                        # Supplies this item to the surrounding call or collection.
                        challenge.show_creator_name,
                        # Calls `json.dumps` with the supplied values.
                        json.dumps(challenge.config, ensure_ascii=False, sort_keys=True),
                        # Calls `ensure_aware` with the supplied values.
                        ensure_aware(challenge.created_at).isoformat(),
                        # Calls `ensure_aware` with the supplied values.
                        ensure_aware(challenge.expires_at).isoformat(),
                        # Begins the nested block or multiline expression completed below.
                        (
                            # Calls `ensure_aware` with the supplied values.
                            ensure_aware(challenge.revoked_at).isoformat()
                            # Checks this condition before executing the nested branch.
                            if challenge.revoked_at
                            # Executes this statement as the next step in the surrounding logic.
                            else ""
                            # Closes the multiline call, declaration, or collection started above.
                        ),
                        # Closes the multiline call, declaration, or collection started above.
                    ]
                    # Iterates through the supplied values for the nested operation.
                    for challenge in challenges
                    # Closes the multiline call, declaration, or collection started above.
                ],
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `output.writestr` with the supplied values.
        output.writestr(
            # Supplies this item to the surrounding call or collection.
            "rooms.csv",
            # Calls `_csv_document` with the supplied values.
            _csv_document(
                # Supplies this item to the surrounding call or collection.
                ["room_id", "status", "joined_at", "expires_at", "is_tie", "won"],
                # Begins the nested block or multiline expression completed below.
                [
                    # Begins the nested block or multiline expression completed below.
                    [
                        # Supplies this item to the surrounding call or collection.
                        room.id,
                        # Supplies this item to the surrounding call or collection.
                        room.status,
                        # Calls `ensure_aware` with the supplied values.
                        ensure_aware(member.joined_at).isoformat(),
                        # Calls `ensure_aware` with the supplied values.
                        ensure_aware(room.expires_at).isoformat(),
                        # Supplies this item to the surrounding call or collection.
                        room.is_tie,
                        # Supplies this item to the surrounding call or collection.
                        room.winner_id == principal.user_id,
                        # Closes the multiline call, declaration, or collection started above.
                    ]
                    # Iterates through the supplied values for the nested operation.
                    for member, room in memberships
                    # Closes the multiline call, declaration, or collection started above.
                ],
                # Closes the multiline call, declaration, or collection started above.
            ),
            # Closes the multiline call, declaration, or collection started above.
        )
    # Returns this result to the caller and ends the current function.
    return archive.getvalue()


# Defines the `delete_account` callable and its typed interface.
async def delete_account(session: MongoSession, principal: AuthPrincipal) -> None:
    # Computes and stores `profile` for subsequent operations.
    profile = await session.get(Profile, principal.user_id)
    # Checks this condition before executing the nested branch.
    if profile is None:
        # Computes and stores `profile` for subsequent operations.
        profile = await ensure_profile(session, principal)
    # Checks this condition before executing the nested branch.
    if profile.deleted_at is not None:
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `profile.display_name` for subsequent operations.
    profile.display_name = None
    # Computes and stores `profile.normalized_display_name` for subsequent operations.
    profile.normalized_display_name = None
    # Computes and stores `profile.is_anonymous` for subsequent operations.
    profile.is_anonymous = True
    # Computes and stores `profile.public_leaderboards` for subsequent operations.
    profile.public_leaderboards = False
    # Computes and stores `profile.deleted_at` for subsequent operations.
    profile.deleted_at = utcnow()
    # Waits for this asynchronous operation to complete.
    await session.update_many(
        # Supplies this required nested value.
        LeaderboardEntry,
        # Supplies this required nested value.
        {"user_id": principal.user_id},
        # Supplies this required nested value.
        {"$set": {"invalidated_at": utcnow(), "review_status": "deleted_account"}},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Waits for this asynchronous operation to complete.
    await session.update_many(
        # Supplies this required nested value.
        FriendChallenge,
        # Supplies this required nested value.
        {"creator_id": principal.user_id},
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            "$set": {
                # Supplies this literal value to the surrounding declaration or call.
                "revoked_at": utcnow(),
                # Supplies this literal value to the surrounding declaration or call.
                "title": None,
                # Supplies this literal value to the surrounding declaration or call.
                "show_creator_name": False,
                # Closes the multiline declaration, call, or collection opened above.
            }
            # Closes the multiline declaration, call, or collection opened above.
        },
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Waits for this asynchronous operation to complete.
    await session.update_many(
        # Supplies this required nested value.
        MultiplayerRoom,
        # Supplies this required nested value.
        {"owner_id": principal.user_id, "status": {"$in": ["waiting", "active"]}},
        # Supplies this required nested value.
        {"$set": {"status": "terminated"}},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Waits for this asynchronous operation to complete.
    await session.delete_many(UserAchievement, {"user_id": principal.user_id})
    # Waits for this asynchronous operation to complete.
    await session.delete_many(SupportRequest, {"user_id": principal.user_id})
    # Waits for this asynchronous operation to complete.
    await session.delete_many(AdminGrant, {"user_id": principal.user_id})
    # Calls `session.add` with the supplied values.
    session.add(
        # Calls `AuditEvent` with the supplied values.
        AuditEvent(
            # Provides the `actor_id` parameter or keyword argument.
            actor_id=principal.user_id,
            # Provides the `action` parameter or keyword argument.
            action="account.deleted",
            # Provides the `target_type` parameter or keyword argument.
            target_type="profile",
            # Provides the `target_id` parameter or keyword argument.
            target_id=str(principal.user_id),
            # Provides the `event_data` parameter or keyword argument.
            event_data={},
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
