# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `re` so the module can use that dependency.
import re

# Imports `unicodedata` so the module can use that dependency.
import unicodedata

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `datetime` for use in this module.
from datetime import date, datetime

# Imports selected names from `typing` for use in this module.
from typing import Literal

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import CodeMakerType, GameMode, GameVisibility

# Imports selected names from `pydantic` for use in this module.
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Computes and stores `_UNSAFE_UNICODE_CATEGORIES` for subsequent operations.
_UNSAFE_UNICODE_CATEGORIES = {"Cc", "Cf"}


# Defines the `normalize_user_text` callable and its typed interface.
def normalize_user_text(value: str) -> str:
    # Documents the purpose or contract of this module, class, or function.
    """Normalize user-authored labels before policy and length validation."""

    # Computes and stores `normalized` for subsequent operations.
    normalized = unicodedata.normalize("NFKC", value)
    # Checks this condition before executing the nested branch.
    if any(
        # Calls `unicodedata.category` with the supplied values.
        unicodedata.category(character) in _UNSAFE_UNICODE_CATEGORIES
        # Continues the surrounding expression or operation.
        for character in normalized
        # Begins the nested block or multiline expression completed below.
    ):
        # Raises this exception to report an invalid or failed operation.
        raise ValueError("Text cannot contain control or bidirectional formatting characters.")
    # Returns this result to the caller and ends the current function.
    return " ".join(normalized.split())


# Defines the `to_camel` callable and its typed interface.
def to_camel(value: str) -> str:
    # Executes this statement as the next step in the surrounding logic.
    first, *rest = value.split("_")
    # Returns this result to the caller and ends the current function.
    return first + "".join(part.capitalize() for part in rest)


# Defines the `APIModel` class and its related behavior.
class APIModel(BaseModel):
    # Computes and stores `model_config` for subsequent operations.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


# Defines the `ErrorResponse` class and its related behavior.
class ErrorResponse(APIModel):
    # Declares the typed `code` data field.
    code: str
    # Declares the typed `message` data field.
    message: str
    # Declares the typed `request_id` data field.
    request_id: str


# Defines the `GameConfigSchema` class and its related behavior.
class GameConfigSchema(APIModel):
    # Computes and stores `colours` for subsequent operations.
    colours: list[str] = Field(min_length=5, max_length=10)
    # Computes and stores `code_length` for subsequent operations.
    code_length: int = Field(ge=3, le=6)
    # Computes and stores `max_attempts` for subsequent operations.
    max_attempts: int = Field(ge=1, le=20)
    # Declares the typed `duplicates_allowed` data field.
    duplicates_allowed: bool
    # Computes and stores `code_maker` for subsequent operations.
    code_maker: CodeMakerType = CodeMakerType.COMPUTER
    # Computes and stores `visibility` for subsequent operations.
    visibility: GameVisibility = GameVisibility.PRIVATE
    # Computes and stores `ranked` for subsequent operations.
    ranked: bool = False
    # Computes and stores `time_bonus_cap` for subsequent operations.
    time_bonus_cap: int = Field(default=300, ge=0, le=3600)


# Defines the `CreateGameRequest` class and its related behavior.
class CreateGameRequest(APIModel):
    # Computes and stores `mode` for subsequent operations.
    mode: GameMode = GameMode.SOLO
    # Computes and stores `difficulty` for subsequent operations.
    difficulty: Literal["easy", "normal", "hard", "expert"] | None = None
    # Computes and stores `config` for subsequent operations.
    config: GameConfigSchema | None = None
    # Computes and stores `secret` for subsequent operations.
    secret: list[str] | None = None
    # Computes and stores `idempotency_key` for subsequent operations.
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=80)

    # Applies `@model_validator(mode="after")` to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines the `validate_selection` callable and its typed interface.
    def validate_selection(self) -> CreateGameRequest:
        # Checks this condition before executing the nested branch.
        if self.difficulty is None and self.config is None:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Choose a difficulty or provide a custom configuration.")
        # Checks this condition before executing the nested branch.
        if self.difficulty is not None and self.config is not None:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Choose either a difficulty or a custom configuration, not both.")
        # Returns this result to the caller and ends the current function.
        return self


# Defines the `AttemptRequest` class and its related behavior.
class AttemptRequest(APIModel):
    # Computes and stores `guess` for subsequent operations.
    guess: list[str] = Field(min_length=1, max_length=6)
    # Computes and stores `idempotency_key` for subsequent operations.
    idempotency_key: str = Field(min_length=12, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$")


# Defines the `FeedbackSchema` class and its related behavior.
class FeedbackSchema(APIModel):
    # Computes and stores `black` for subsequent operations.
    black: int = Field(ge=0, le=6)
    # Computes and stores `white` for subsequent operations.
    white: int = Field(ge=0, le=6)


# Defines the `AttemptSchema` class and its related behavior.
class AttemptSchema(APIModel):
    # Declares the typed `number` data field.
    number: int
    # Declares the typed `guess` data field.
    guess: list[str]
    # Declares the typed `feedback` data field.
    feedback: FeedbackSchema
    # Declares the typed `submitted_at` data field.
    submitted_at: datetime


# Defines the `ScoreBreakdownSchema` class and its related behavior.
class ScoreBreakdownSchema(APIModel):
    # Declares the typed `attempts` data field.
    attempts: int
    # Declares the typed `difficulty` data field.
    difficulty: int
    # Declares the typed `time` data field.
    time: int
    # Declares the typed `total` data field.
    total: int
    # Declares the typed `version` data field.
    version: str


# Defines the `GameResponse` class and its related behavior.
class GameResponse(APIModel):
    # Declares the typed `id` data field.
    id: str
    # Declares the typed `mode` data field.
    mode: str
    # Declares the typed `status` data field.
    status: str
    # Declares the typed `difficulty` data field.
    difficulty: str | None
    # Declares the typed `config` data field.
    config: GameConfigSchema
    # Declares the typed `attempts` data field.
    attempts: list[AttemptSchema]
    # Declares the typed `attempts_used` data field.
    attempts_used: int
    # Declares the typed `max_attempts` data field.
    max_attempts: int
    # Declares the typed `attempts_remaining` data field.
    attempts_remaining: int
    # Declares the typed `started_at` data field.
    started_at: datetime
    # Declares the typed `completed_at` data field.
    completed_at: datetime | None
    # Declares the typed `score` data field.
    score: int | None
    # Declares the typed `score_breakdown` data field.
    score_breakdown: ScoreBreakdownSchema | None
    # Computes and stores `secret` for subsequent operations.
    secret: list[str] | None = None
    # Declares the typed `ranked` data field.
    ranked: bool


# Defines the `DailyDefinitionResponse` class and its related behavior.
class DailyDefinitionResponse(APIModel):
    # Declares the typed `id` data field.
    id: str
    # Declares the typed `date` data field.
    date: date
    # Declares the typed `rule_set_version` data field.
    rule_set_version: str
    # Declares the typed `derivation_version` data field.
    derivation_version: str
    # Declares the typed `config` data field.
    config: GameConfigSchema
    # Declares the typed `rollover_at` data field.
    rollover_at: datetime


# Defines the `CreateChallengeRequest` class and its related behavior.
class CreateChallengeRequest(APIModel):
    # Computes and stores `difficulty` for subsequent operations.
    difficulty: Literal["easy", "normal", "hard", "expert"] | None = None
    # Computes and stores `config` for subsequent operations.
    config: GameConfigSchema | None = None
    # Computes and stores `secret` for subsequent operations.
    secret: list[str] | None = None
    # Computes and stores `title` for subsequent operations.
    title: str | None = Field(default=None, max_length=80)
    # Computes and stores `show_creator_name` for subsequent operations.
    show_creator_name: bool = True
    # Computes and stores `idempotency_key` for subsequent operations.
    idempotency_key: str | None = Field(
        # Computes and stores `default` for subsequent operations.
        default=None,
        # Provides the `min_length` value to the surrounding call.
        min_length=12,
        # Provides the `max_length` value to the surrounding call.
        max_length=80,
        # Provides the `pattern` value to the surrounding call.
        pattern=r"^[A-Za-z0-9._:-]+$",
        # Closes the multiline call, declaration, or collection started above.
    )

    # Applies `@field_validator("title", mode="before")` to configure the declaration immediately
    # below.
    @field_validator("title", mode="before")
    # Applies `@classmethod` to configure the declaration immediately below.
    @classmethod
    # Defines the `sanitize_title` callable and its typed interface.
    def sanitize_title(cls, value: str | None) -> str | None:
        # Checks this condition before executing the nested branch.
        if value is None:
            # Returns this result to the caller and ends the current function.
            return None
        # Computes and stores `normalized` for subsequent operations.
        normalized = normalize_user_text(value)
        # Checks this condition before executing the nested branch.
        if not normalized:
            # Returns this result to the caller and ends the current function.
            return None
        # Returns this result to the caller and ends the current function.
        return normalized

    # Applies `@model_validator(mode="after")` to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines the `validate_selection` callable and its typed interface.
    def validate_selection(self) -> CreateChallengeRequest:
        # Checks this condition before executing the nested branch.
        if (self.difficulty is None) == (self.config is None):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Choose exactly one difficulty or custom configuration.")
        # Returns this result to the caller and ends the current function.
        return self


# Defines the `ChallengeResponse` class and its related behavior.
class ChallengeResponse(APIModel):
    # Computes and stores `id` for subsequent operations.
    id: str | None = None
    # Declares the typed `share_code` data field.
    share_code: str
    # Declares the typed `title` data field.
    title: str | None
    # Declares the typed `creator_name` data field.
    creator_name: str | None
    # Declares the typed `config` data field.
    config: GameConfigSchema
    # Declares the typed `expires_at` data field.
    expires_at: datetime
    # Declares the typed `revoked` data field.
    revoked: bool
    # Computes and stores `completed_count` for subsequent operations.
    completed_count: int = 0


# Defines the `OwnedChallengeItem` class and its related behavior.
class OwnedChallengeItem(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `title` data field.
    title: str | None
    # Declares the typed `show_creator_name` data field.
    show_creator_name: bool
    # Declares the typed `config` data field.
    config: GameConfigSchema
    # Declares the typed `revoked` data field.
    revoked: bool
    # Declares the typed `expires_at` data field.
    expires_at: datetime
    # Declares the typed `completed_count` data field.
    completed_count: int
    # Declares the typed `created_at` data field.
    created_at: datetime


# Defines the `PaginatedOwnedChallenges` class and its related behavior.
class PaginatedOwnedChallenges(APIModel):
    # Declares the typed `items` data field.
    items: list[OwnedChallengeItem]
    # Declares the typed `page` data field.
    page: int
    # Declares the typed `page_size` data field.
    page_size: int
    # Declares the typed `total` data field.
    total: int


# Defines the `CreateRoomRequest` class and its related behavior.
class CreateRoomRequest(APIModel):
    # Computes and stores `difficulty` for subsequent operations.
    difficulty: Literal["easy", "normal", "hard", "expert"] = "normal"
    # Computes and stores `idempotency_key` for subsequent operations.
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=80)


# Defines the `RoomMemberResponse` class and its related behavior.
class RoomMemberResponse(APIModel):
    # Declares the typed `user_id` data field.
    user_id: uuid.UUID
    # Declares the typed `display_name` data field.
    display_name: str
    # Declares the typed `connected` data field.
    connected: bool
    # Declares the typed `ready` data field.
    ready: bool
    # Declares the typed `ready_at` data field.
    ready_at: datetime | None
    # Declares the typed `attempts_used` data field.
    attempts_used: int
    # Declares the typed `completed` data field.
    completed: bool
    # Declares the typed `game_id` data field.
    game_id: str | None


# Defines the `RoomResponse` class and its related behavior.
class RoomResponse(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Computes and stores `room_code` for subsequent operations.
    room_code: str | None = None
    # Declares the typed `status` data field.
    status: str
    # Declares the typed `config` data field.
    config: GameConfigSchema
    # Declares the typed `members` data field.
    members: list[RoomMemberResponse]
    # Declares the typed `winner_id` data field.
    winner_id: uuid.UUID | None
    # Declares the typed `is_tie` data field.
    is_tie: bool
    # Declares the typed `expires_at` data field.
    expires_at: datetime
    # Declares the typed `event_sequence` data field.
    event_sequence: int


# Defines the `LeaderboardItem` class and its related behavior.
class LeaderboardItem(APIModel):
    # Declares the typed `rank` data field.
    rank: int
    # Declares the typed `display_name` data field.
    display_name: str
    # Declares the typed `score` data field.
    score: int
    # Declares the typed `attempts_used` data field.
    attempts_used: int
    # Declares the typed `elapsed_seconds` data field.
    elapsed_seconds: int
    # Declares the typed `completed_at` data field.
    completed_at: datetime
    # Declares the typed `is_current_user` data field.
    is_current_user: bool


# Defines the `PaginatedLeaderboard` class and its related behavior.
class PaginatedLeaderboard(APIModel):
    # Declares the typed `items` data field.
    items: list[LeaderboardItem]
    # Declares the typed `page` data field.
    page: int
    # Declares the typed `page_size` data field.
    page_size: int
    # Declares the typed `total` data field.
    total: int
    # Declares the typed `current_user_rank` data field.
    current_user_rank: int | None


# Defines the `ProfileResponse` class and its related behavior.
class ProfileResponse(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `display_name` data field.
    display_name: str | None
    # Declares the typed `is_anonymous` data field.
    is_anonymous: bool
    # Declares the typed `public_leaderboards` data field.
    public_leaderboards: bool
    # Declares the typed `created_at` data field.
    created_at: datetime


# Defines the `ProfileUpdateRequest` class and its related behavior.
class ProfileUpdateRequest(APIModel):
    # Computes and stores `display_name` for subsequent operations.
    display_name: str | None = Field(default=None, min_length=2, max_length=32)
    # Computes and stores `public_leaderboards` for subsequent operations.
    public_leaderboards: bool | None = None

    # Applies `@field_validator("display_name", mode="before")` to configure the declaration
    # immediately below.
    @field_validator("display_name", mode="before")
    # Applies `@classmethod` to configure the declaration immediately below.
    @classmethod
    # Defines the `validate_display_name` callable and its typed interface.
    def validate_display_name(cls, value: str | None) -> str | None:
        # Checks this condition before executing the nested branch.
        if value is None:
            # Returns this result to the caller and ends the current function.
            return None
        # Computes and stores `normalized` for subsequent operations.
        normalized = normalize_user_text(value)
        # Checks this condition before executing the nested branch.
        if not re.fullmatch(r"[\w\- .'\u3400-\u9fff]+", normalized, re.UNICODE):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Display name contains unsupported characters.")
        # Computes and stores `reserved` for subsequent operations.
        reserved = {"admin", "administrator", "system", "moderator", "mastermind"}
        # Checks this condition before executing the nested branch.
        if normalized.casefold() in reserved:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("That display name is reserved.")
        # Returns this result to the caller and ends the current function.
        return normalized


# Defines the `AchievementProgressSchema` class and its related behavior.
class AchievementProgressSchema(APIModel):
    # Computes and stores `current` for subsequent operations.
    current: int = Field(ge=0, le=1000)
    # Computes and stores `target` for subsequent operations.
    target: int = Field(ge=1, le=1000)

    # Applies `@model_validator(mode="after")` to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines the `validate_progress` callable and its typed interface.
    def validate_progress(self) -> AchievementProgressSchema:
        # Checks this condition before executing the nested branch.
        if self.current > self.target:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Achievement progress cannot exceed its target.")
        # Returns this result to the caller and ends the current function.
        return self


# Defines the `StatsResponse` class and its related behavior.
class StatsResponse(APIModel):
    # Declares the typed `games_played` data field.
    games_played: int
    # Declares the typed `games_won` data field.
    games_won: int
    # Declares the typed `games_lost` data field.
    games_lost: int
    # Declares the typed `games_abandoned` data field.
    games_abandoned: int
    # Declares the typed `win_rate` data field.
    win_rate: float
    # Declares the typed `average_attempts_on_wins` data field.
    average_attempts_on_wins: float | None
    # Declares the typed `best_score_by_difficulty` data field.
    best_score_by_difficulty: dict[str, int]
    # Declares the typed `daily_streak` data field.
    daily_streak: int
    # Declares the typed `daily_completion_history` data field.
    daily_completion_history: list[date]
    # Declares the typed `fastest_eligible_solve` data field.
    fastest_eligible_solve: int | None
    # Declares the typed `total_black_pegs` data field.
    total_black_pegs: int
    # Declares the typed `total_white_pegs` data field.
    total_white_pegs: int
    # Declares the typed `favourite_mode` data field.
    favourite_mode: str | None
    # Declares the typed `achievements` data field.
    achievements: list[str]
    # Computes and stores `achievement_progress` for subsequent operations.
    achievement_progress: dict[str, AchievementProgressSchema] = Field(max_length=10)


# Defines the `PaginatedGames` class and its related behavior.
class PaginatedGames(APIModel):
    # Declares the typed `items` data field.
    items: list[GameResponse]
    # Declares the typed `page` data field.
    page: int
    # Declares the typed `page_size` data field.
    page_size: int
    # Declares the typed `total` data field.
    total: int


# Defines the `DeleteAccountResponse` class and its related behavior.
class DeleteAccountResponse(APIModel):
    # Declares the typed `deleted` data field.
    deleted: bool


# Defines the `DeleteAccountRequest` class and its related behavior.
class DeleteAccountRequest(APIModel):
    # Declares the typed `confirmation` data field.
    confirmation: Literal["DELETE"]


# Defines the `AnalyticsEventRequest` class and its related behavior.
class AnalyticsEventRequest(APIModel):
    # Declares the typed `client_event_id` data field.
    client_event_id: uuid.UUID
    # Declares the typed `event_name` data field.
    event_name: Literal[
        # Supplies this item to the surrounding call or collection.
        "game_started",
        # Supplies this item to the surrounding call or collection.
        "game_completed",
        # Supplies this item to the surrounding call or collection.
        "game_abandoned",
        # Supplies this item to the surrounding call or collection.
        "difficulty_selected",
        # Supplies this item to the surrounding call or collection.
        "daily_completed",
        # Supplies this item to the surrounding call or collection.
        "friend_challenge_created",
        # Supplies this item to the surrounding call or collection.
        "room_joined",
        # Supplies this item to the surrounding call or collection.
        "duel_completed",
        # Supplies this item to the surrounding call or collection.
        "validation_error",
        # Supplies this item to the surrounding call or collection.
        "reconnect",
        # Supplies this item to the surrounding call or collection.
        "account_upgraded",
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Declares the typed `consent` data field.
    consent: Literal[True]
    # Declares the typed `consent_version` data field.
    consent_version: Literal["privacy-v1"]
    # Declares the typed `locale` data field.
    locale: Literal["en", "zh-Hant"]
    # Declares the typed `mode` data field.
    mode: (
        # Executes this statement as the next step in the surrounding logic.
        Literal["solo", "daily", "practice", "pass_and_play", "friend_challenge", "duel"] | None
        # Executes this statement as the next step in the surrounding logic.
    ) = None
    # Computes and stores `difficulty` for subsequent operations.
    difficulty: Literal["easy", "normal", "hard", "expert", "custom"] | None = None
    # Computes and stores `result` for subsequent operations.
    result: Literal["won", "lost", "abandoned", "expired", "tie"] | None = None
    # Computes and stores `attempts_used` for subsequent operations.
    attempts_used: int | None = Field(default=None, ge=0, le=20)
    # Computes and stores `ranked` for subsequent operations.
    ranked: bool | None = None
    # Computes and stores `score_band` for subsequent operations.
    score_band: Literal["zero", "1-999", "1000-1499", "1500+"] | None = None
    # Computes and stores `daily_challenge_id` for subsequent operations.
    daily_challenge_id: str | None = Field(
        # Computes and stores `default` for subsequent operations.
        default=None,
        # Provides the `min_length` value to the surrounding call.
        min_length=10,
        # Provides the `max_length` value to the surrounding call.
        max_length=64,
        # Provides the `pattern` value to the surrounding call.
        pattern=r"^[A-Za-z0-9:_-]+$",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `official` for subsequent operations.
    official: bool | None = None
    # Computes and stores `expiry_band` for subsequent operations.
    expiry_band: Literal["30_days"] | None = None
    # Computes and stores `room_state` for subsequent operations.
    room_state: Literal["waiting", "active", "completed", "expired", "terminated"] | None = None
    # Computes and stores `reconnect` for subsequent operations.
    reconnect: bool | None = None
    # Computes and stores `tie` for subsequent operations.
    tie: bool | None = None
    # Declares the typed `validation_category` data field.
    validation_category: (
        # Executes this statement as the next step in the surrounding logic.
        Literal["game_config", "guess", "challenge", "room", "profile", "auth"] | None
        # Executes this statement as the next step in the surrounding logic.
    ) = None
    # Computes and stores `surface` for subsequent operations.
    surface: Literal["game", "room", "daily", "challenge", "account"] | None = None
    # Computes and stores `recovered` for subsequent operations.
    recovered: bool | None = None
    # Computes and stores `previous_anonymous` for subsequent operations.
    previous_anonymous: bool | None = None

    # Applies `@model_validator(mode="after")` to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines the `validate_event_shape` callable and its typed interface.
    def validate_event_shape(self) -> AnalyticsEventRequest:
        # Computes and stores `event_fields` for subsequent operations.
        event_fields = {
            # Associates the `game_started` key with its value.
            "game_started": {"mode", "difficulty"},
            # Associates the `game_completed` key with its value.
            "game_completed": {
                # Supplies this item to the surrounding call or collection.
                "mode",
                # Supplies this item to the surrounding call or collection.
                "result",
                # Supplies this item to the surrounding call or collection.
                "attempts_used",
                # Supplies this item to the surrounding call or collection.
                "ranked",
                # Supplies this item to the surrounding call or collection.
                "score_band",
                # Closes the multiline call, declaration, or collection started above.
            },
            # Associates the `game_abandoned` key with its value.
            "game_abandoned": {"mode", "attempts_used"},
            # Associates the `difficulty_selected` key with its value.
            "difficulty_selected": {"difficulty"},
            # Associates the `daily_completed` key with its value.
            "daily_completed": {"daily_challenge_id", "result", "attempts_used"},
            # Associates the `friend_challenge_created` key with its value.
            "friend_challenge_created": {"official", "expiry_band"},
            # Associates the `room_joined` key with its value.
            "room_joined": {"room_state", "reconnect"},
            # Associates the `duel_completed` key with its value.
            "duel_completed": {"result", "attempts_used", "tie"},
            # Associates the `validation_error` key with its value.
            "validation_error": {"validation_category"},
            # Associates the `reconnect` key with its value.
            "reconnect": {"surface", "recovered"},
            # Associates the `account_upgraded` key with its value.
            "account_upgraded": {"previous_anonymous"},
            # Closes the multiline call, declaration, or collection started above.
        }
        # Computes and stores `common` for subsequent operations.
        common = {"client_event_id", "event_name", "consent", "consent_version", "locale"}
        # Computes and stores `supplied` for subsequent operations.
        supplied = self.model_fields_set - common
        # Computes and stores `expected` for subsequent operations.
        expected = event_fields[self.event_name]
        # Checks this condition before executing the nested branch.
        if supplied != expected or any(getattr(self, field) is None for field in expected):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The analytics event properties do not match the event name.")
        # Checks this condition before executing the nested branch.
        if self.event_name == "account_upgraded" and self.previous_anonymous is not True:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("An account upgrade must follow an anonymous identity.")
        # Checks this condition before executing the nested branch.
        if self.event_name == "duel_completed" and (self.tie is True) != (self.result == "tie"):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Duel tie fields are inconsistent.")
        # Returns this result to the caller and ends the current function.
        return self


# Defines the `AnalyticsEventResponse` class and its related behavior.
class AnalyticsEventResponse(APIModel):
    # Declares the typed `received` data field.
    received: bool


# Defines the `StartGameRequest` class and its related behavior.
class StartGameRequest(APIModel):
    # Computes and stores `practice` for subsequent operations.
    practice: bool = False


# Defines the `AdminSummary` class and its related behavior.
class AdminSummary(APIModel):
    # Declares the typed `profiles` data field.
    profiles: int
    # Declares the typed `active_games` data field.
    active_games: int
    # Declares the typed `completed_games` data field.
    completed_games: int
    # Declares the typed `active_rooms` data field.
    active_rooms: int
    # Declares the typed `pending_review_entries` data field.
    pending_review_entries: int


# Defines the `AdminActionRequest` class and its related behavior.
class AdminActionRequest(APIModel):
    # Computes and stores `reason` for subsequent operations.
    reason: str = Field(min_length=3, max_length=300)
    # Computes and stores `enabled` for subsequent operations.
    enabled: bool | None = None
    # Computes and stores `display_name` for subsequent operations.
    display_name: str | None = Field(default=None, max_length=32)


# Defines the `FeatureFlagResponse` class and its related behavior.
class FeatureFlagResponse(APIModel):
    # Declares the typed `key` data field.
    key: str
    # Declares the typed `enabled` data field.
    enabled: bool


# Defines the `AuditEventResponse` class and its related behavior.
class AuditEventResponse(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `actor_id` data field.
    actor_id: uuid.UUID | None
    # Declares the typed `action` data field.
    action: str
    # Declares the typed `target_type` data field.
    target_type: str
    # Declares the typed `target_id` data field.
    target_id: str
    # Declares the typed `reason` data field.
    reason: str | None
    # Declares the typed `created_at` data field.
    created_at: datetime


# Defines the `RoomClientMessage` class and its related behavior.
class RoomClientMessage(APIModel):
    # Declares the typed `version` data field.
    version: Literal[1]
    # Declares the typed `type` data field.
    type: Literal["guess", "heartbeat"]
    # Computes and stores `guess` for subsequent operations.
    guess: list[str] | None = None
    # Computes and stores `idempotency_key` for subsequent operations.
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=80)

    # Applies `@model_validator(mode="after")` to configure the declaration immediately below.
    @model_validator(mode="after")
    # Defines the `validate_guess_event` callable and its typed interface.
    def validate_guess_event(self) -> RoomClientMessage:
        # Checks this condition before executing the nested branch.
        if self.type == "guess" and (self.guess is None or self.idempotency_key is None):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Guess events require a guess and idempotency key.")
        # Returns this result to the caller and ends the current function.
        return self


# Defines the `WebSocketTicketResponse` class and its related behavior.
class WebSocketTicketResponse(APIModel):
    # Declares the typed `ticket` data field.
    ticket: str
    # Declares the typed `expires_at` data field.
    expires_at: datetime


# Defines the `SupportRequestCreate` class and its related behavior.
class SupportRequestCreate(APIModel):
    # Declares the typed `topic` data field.
    topic: Literal["account", "gameplay", "accessibility", "privacy", "safety", "other"]
    # Computes and stores `reply_email` for subsequent operations.
    reply_email: str = Field(min_length=3, max_length=254)
    # Computes and stores `message` for subsequent operations.
    message: str = Field(min_length=10, max_length=4000)

    # Applies `@field_validator("reply_email")` to configure the declaration immediately below.
    @field_validator("reply_email")
    # Applies `@classmethod` to configure the declaration immediately below.
    @classmethod
    # Defines the `validate_reply_email` callable and its typed interface.
    def validate_reply_email(cls, value: str) -> str:
        # Computes and stores `normalized` for subsequent operations.
        normalized = value.strip().casefold()
        # Checks this condition before executing the nested branch.
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[1]:
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Enter a valid reply email address.")
        # Checks this condition before executing the nested branch.
        if any(ord(character) < 33 for character in normalized):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("Enter a valid reply email address.")
        # Returns this result to the caller and ends the current function.
        return normalized

    # Applies `@field_validator("message")` to configure the declaration immediately below.
    @field_validator("message")
    # Applies `@classmethod` to configure the declaration immediately below.
    @classmethod
    # Defines the `normalize_message` callable and its typed interface.
    def normalize_message(cls, value: str) -> str:
        # Computes and stores `normalized` for subsequent operations.
        normalized = value.strip()
        # Checks this condition before executing the nested branch.
        if any(character == "\x00" for character in normalized):
            # Raises this exception to report an invalid or failed operation.
            raise ValueError("The message contains an unsupported character.")
        # Returns this result to the caller and ends the current function.
        return normalized


# Defines the `SupportRequestResponse` class and its related behavior.
class SupportRequestResponse(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `received` data field.
    received: bool


# Defines the `AdminGameItem` class and its related behavior.
class AdminGameItem(APIModel):
    # Declares the typed `id` data field.
    id: str
    # Declares the typed `owner_id` data field.
    owner_id: uuid.UUID
    # Declares the typed `mode` data field.
    mode: str
    # Declares the typed `status` data field.
    status: str
    # Declares the typed `difficulty` data field.
    difficulty: str | None
    # Declares the typed `attempts_used` data field.
    attempts_used: int
    # Declares the typed `max_attempts` data field.
    max_attempts: int
    # Declares the typed `score` data field.
    score: int | None
    # Declares the typed `ranked_eligibility` data field.
    ranked_eligibility: str
    # Declares the typed `started_at` data field.
    started_at: datetime
    # Declares the typed `completed_at` data field.
    completed_at: datetime | None


# Defines the `AdminProfileItem` class and its related behavior.
class AdminProfileItem(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `display_name` data field.
    display_name: str | None
    # Declares the typed `is_anonymous` data field.
    is_anonymous: bool
    # Declares the typed `public_leaderboards` data field.
    public_leaderboards: bool
    # Declares the typed `is_banned` data field.
    is_banned: bool
    # Declares the typed `deleted_at` data field.
    deleted_at: datetime | None
    # Declares the typed `created_at` data field.
    created_at: datetime


# Defines the `AdminRoomItem` class and its related behavior.
class AdminRoomItem(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `status` data field.
    status: str
    # Declares the typed `member_count` data field.
    member_count: int
    # Declares the typed `winner_id` data field.
    winner_id: uuid.UUID | None
    # Declares the typed `is_tie` data field.
    is_tie: bool
    # Declares the typed `expires_at` data field.
    expires_at: datetime
    # Declares the typed `created_at` data field.
    created_at: datetime


# Defines the `AdminChallengeItem` class and its related behavior.
class AdminChallengeItem(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `creator_id` data field.
    creator_id: uuid.UUID
    # Declares the typed `title` data field.
    title: str | None
    # Declares the typed `completed_count` data field.
    completed_count: int
    # Declares the typed `revoked_at` data field.
    revoked_at: datetime | None
    # Declares the typed `expires_at` data field.
    expires_at: datetime
    # Declares the typed `created_at` data field.
    created_at: datetime


# Defines the `AdminLeaderboardItem` class and its related behavior.
class AdminLeaderboardItem(APIModel):
    # Declares the typed `id` data field.
    id: uuid.UUID
    # Declares the typed `game_id` data field.
    game_id: uuid.UUID
    # Declares the typed `user_id` data field.
    user_id: uuid.UUID
    # Declares the typed `category` data field.
    category: str
    # Declares the typed `score` data field.
    score: int
    # Declares the typed `attempts_used` data field.
    attempts_used: int
    # Declares the typed `elapsed_seconds` data field.
    elapsed_seconds: int
    # Declares the typed `review_status` data field.
    review_status: str
    # Declares the typed `invalidated_at` data field.
    invalidated_at: datetime | None
    # Declares the typed `completed_at` data field.
    completed_at: datetime


# Defines the `AdminPage` class and its related behavior.
class AdminPage[AdminItem](APIModel):
    # Declares the typed `items` data field.
    items: list[AdminItem]
    # Declares the typed `page` data field.
    page: int
    # Declares the typed `page_size` data field.
    page_size: int
    # Declares the typed `total` data field.
    total: int


# Defines the `ChallengeResultItem` class and its related behavior.
class ChallengeResultItem(APIModel):
    # Computes and stores `rank` for subsequent operations.
    rank: int = Field(ge=1)
    # Declares the typed `player_label` data field.
    player_label: str
    # Declares the typed `result` data field.
    result: str
    # Declares the typed `attempts_used` data field.
    attempts_used: int
    # Declares the typed `max_attempts` data field.
    max_attempts: int
    # Declares the typed `score` data field.
    score: int
    # Declares the typed `elapsed_seconds` data field.
    elapsed_seconds: int | None
    # Declares the typed `completed_at` data field.
    completed_at: datetime


# Defines the `ChallengeResultsResponse` class and its related behavior.
class ChallengeResultsResponse(APIModel):
    # Declares the typed `completed_count` data field.
    completed_count: int
    # Declares the typed `win_rate` data field.
    win_rate: float
    # Declares the typed `average_attempts` data field.
    average_attempts: float | None
    # Declares the typed `score_distribution` data field.
    score_distribution: dict[str, int]
    # Declares the typed `items` data field.
    items: list[ChallengeResultItem]
    # Declares the typed `page` data field.
    page: int
    # Declares the typed `page_size` data field.
    page_size: int
    # Declares the typed `total` data field.
    total: int
