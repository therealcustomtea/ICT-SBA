from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import date, datetime
from typing import Literal

from mastermind_core import CodeMakerType, GameMode, GameVisibility
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_UNSAFE_UNICODE_CATEGORIES = {"Cc", "Cf"}


def normalize_user_text(value: str) -> str:
    """Normalize user-authored labels before policy and length validation."""

    normalized = unicodedata.normalize("NFKC", value)
    if any(
        unicodedata.category(character) in _UNSAFE_UNICODE_CATEGORIES for character in normalized
    ):
        raise ValueError("Text cannot contain control or bidirectional formatting characters.")
    return " ".join(normalized.split())


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ErrorResponse(APIModel):
    code: str
    message: str
    request_id: str


class GameConfigSchema(APIModel):
    colours: list[str] = Field(min_length=5, max_length=10)
    code_length: int = Field(ge=3, le=6)
    max_attempts: int = Field(ge=1, le=20)
    duplicates_allowed: bool
    code_maker: CodeMakerType = CodeMakerType.COMPUTER
    visibility: GameVisibility = GameVisibility.PRIVATE
    ranked: bool = False
    time_bonus_cap: int = Field(default=300, ge=0, le=3600)


class CreateGameRequest(APIModel):
    mode: GameMode = GameMode.SOLO
    difficulty: Literal["easy", "normal", "hard", "expert"] | None = None
    config: GameConfigSchema | None = None
    secret: list[str] | None = None
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=80)

    @model_validator(mode="after")
    def validate_selection(self) -> CreateGameRequest:
        if self.difficulty is None and self.config is None:
            raise ValueError("Choose a difficulty or provide a custom configuration.")
        if self.difficulty is not None and self.config is not None:
            raise ValueError("Choose either a difficulty or a custom configuration, not both.")
        return self


class AttemptRequest(APIModel):
    guess: list[str] = Field(min_length=1, max_length=6)
    idempotency_key: str = Field(min_length=12, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$")


class FeedbackSchema(APIModel):
    black: int = Field(ge=0, le=6)
    white: int = Field(ge=0, le=6)


class AttemptSchema(APIModel):
    number: int
    guess: list[str]
    feedback: FeedbackSchema
    submitted_at: datetime


class ScoreBreakdownSchema(APIModel):
    attempts: int
    difficulty: int
    time: int
    total: int
    version: str


class GameResponse(APIModel):
    id: str
    mode: str
    status: str
    difficulty: str | None
    config: GameConfigSchema
    attempts: list[AttemptSchema]
    attempts_used: int
    max_attempts: int
    attempts_remaining: int
    started_at: datetime
    completed_at: datetime | None
    score: int | None
    score_breakdown: ScoreBreakdownSchema | None
    secret: list[str] | None = None
    ranked: bool


class DailyDefinitionResponse(APIModel):
    id: str
    date: date
    rule_set_version: str
    derivation_version: str
    config: GameConfigSchema
    rollover_at: datetime


class CreateChallengeRequest(APIModel):
    difficulty: Literal["easy", "normal", "hard", "expert"] | None = None
    config: GameConfigSchema | None = None
    secret: list[str] | None = None
    title: str | None = Field(default=None, max_length=80)
    show_creator_name: bool = True
    idempotency_key: str | None = Field(
        default=None, min_length=12, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$"
    )

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_user_text(value)
        if not normalized:
            return None
        return normalized

    @model_validator(mode="after")
    def validate_selection(self) -> CreateChallengeRequest:
        if (self.difficulty is None) == (self.config is None):
            raise ValueError("Choose exactly one difficulty or custom configuration.")
        return self


class ChallengeResponse(APIModel):
    id: str | None = None
    share_code: str
    title: str | None
    creator_name: str | None
    config: GameConfigSchema
    expires_at: datetime
    revoked: bool
    completed_count: int = 0


class OwnedChallengeItem(APIModel):
    id: uuid.UUID
    title: str | None
    show_creator_name: bool
    config: GameConfigSchema
    revoked: bool
    expires_at: datetime
    completed_count: int
    created_at: datetime


class PaginatedOwnedChallenges(APIModel):
    items: list[OwnedChallengeItem]
    page: int
    page_size: int
    total: int


class CreateRoomRequest(APIModel):
    difficulty: Literal["easy", "normal", "hard", "expert"] = "normal"
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=80)


class RoomMemberResponse(APIModel):
    user_id: uuid.UUID
    display_name: str
    connected: bool
    ready: bool
    ready_at: datetime | None
    attempts_used: int
    completed: bool
    game_id: str | None


class RoomResponse(APIModel):
    id: uuid.UUID
    room_code: str | None = None
    status: str
    config: GameConfigSchema
    members: list[RoomMemberResponse]
    winner_id: uuid.UUID | None
    is_tie: bool
    expires_at: datetime
    event_sequence: int


class LeaderboardItem(APIModel):
    rank: int
    display_name: str
    score: int
    attempts_used: int
    elapsed_seconds: int
    completed_at: datetime
    is_current_user: bool


class PaginatedLeaderboard(APIModel):
    items: list[LeaderboardItem]
    page: int
    page_size: int
    total: int
    current_user_rank: int | None


class ProfileResponse(APIModel):
    id: uuid.UUID
    display_name: str | None
    is_anonymous: bool
    public_leaderboards: bool
    created_at: datetime


class ProfileUpdateRequest(APIModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=32)
    public_leaderboards: bool | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_user_text(value)
        if not re.fullmatch(r"[\w\- .'\u3400-\u9fff]+", normalized, re.UNICODE):
            raise ValueError("Display name contains unsupported characters.")
        reserved = {"admin", "administrator", "system", "moderator", "mastermind"}
        if normalized.casefold() in reserved:
            raise ValueError("That display name is reserved.")
        return normalized


class AchievementProgressSchema(APIModel):
    current: int = Field(ge=0, le=1000)
    target: int = Field(ge=1, le=1000)

    @model_validator(mode="after")
    def validate_progress(self) -> AchievementProgressSchema:
        if self.current > self.target:
            raise ValueError("Achievement progress cannot exceed its target.")
        return self


class StatsResponse(APIModel):
    games_played: int
    games_won: int
    games_lost: int
    games_abandoned: int
    win_rate: float
    average_attempts_on_wins: float | None
    best_score_by_difficulty: dict[str, int]
    daily_streak: int
    daily_completion_history: list[date]
    fastest_eligible_solve: int | None
    total_black_pegs: int
    total_white_pegs: int
    favourite_mode: str | None
    achievements: list[str]
    achievement_progress: dict[str, AchievementProgressSchema] = Field(max_length=10)


class PaginatedGames(APIModel):
    items: list[GameResponse]
    page: int
    page_size: int
    total: int


class DeleteAccountResponse(APIModel):
    deleted: bool


class DeleteAccountRequest(APIModel):
    confirmation: Literal["DELETE"]


class AnalyticsEventRequest(APIModel):
    client_event_id: uuid.UUID
    event_name: Literal[
        "game_started",
        "game_completed",
        "game_abandoned",
        "difficulty_selected",
        "daily_completed",
        "friend_challenge_created",
        "room_joined",
        "duel_completed",
        "validation_error",
        "reconnect",
        "account_upgraded",
    ]
    consent: Literal[True]
    consent_version: Literal["privacy-v1"]
    locale: Literal["en", "zh-Hant"]
    mode: (
        Literal["solo", "daily", "practice", "pass_and_play", "friend_challenge", "duel"] | None
    ) = None
    difficulty: Literal["easy", "normal", "hard", "expert", "custom"] | None = None
    result: Literal["won", "lost", "abandoned", "expired", "tie"] | None = None
    attempts_used: int | None = Field(default=None, ge=0, le=20)
    ranked: bool | None = None
    score_band: Literal["zero", "1-999", "1000-1499", "1500+"] | None = None
    daily_challenge_id: str | None = Field(
        default=None, min_length=10, max_length=64, pattern=r"^[A-Za-z0-9:_-]+$"
    )
    official: bool | None = None
    expiry_band: Literal["30_days"] | None = None
    room_state: Literal["waiting", "active", "completed", "expired", "terminated"] | None = None
    reconnect: bool | None = None
    tie: bool | None = None
    validation_category: (
        Literal["game_config", "guess", "challenge", "room", "profile", "auth"] | None
    ) = None
    surface: Literal["game", "room", "daily", "challenge", "account"] | None = None
    recovered: bool | None = None
    previous_anonymous: bool | None = None

    @model_validator(mode="after")
    def validate_event_shape(self) -> AnalyticsEventRequest:
        event_fields = {
            "game_started": {"mode", "difficulty"},
            "game_completed": {
                "mode",
                "result",
                "attempts_used",
                "ranked",
                "score_band",
            },
            "game_abandoned": {"mode", "attempts_used"},
            "difficulty_selected": {"difficulty"},
            "daily_completed": {"daily_challenge_id", "result", "attempts_used"},
            "friend_challenge_created": {"official", "expiry_band"},
            "room_joined": {"room_state", "reconnect"},
            "duel_completed": {"result", "attempts_used", "tie"},
            "validation_error": {"validation_category"},
            "reconnect": {"surface", "recovered"},
            "account_upgraded": {"previous_anonymous"},
        }
        common = {"client_event_id", "event_name", "consent", "consent_version", "locale"}
        supplied = self.model_fields_set - common
        expected = event_fields[self.event_name]
        if supplied != expected or any(getattr(self, field) is None for field in expected):
            raise ValueError("The analytics event properties do not match the event name.")
        if self.event_name == "account_upgraded" and self.previous_anonymous is not True:
            raise ValueError("An account upgrade must follow an anonymous identity.")
        if self.event_name == "duel_completed" and (self.tie is True) != (self.result == "tie"):
            raise ValueError("Duel tie fields are inconsistent.")
        return self


class AnalyticsEventResponse(APIModel):
    received: bool


class StartGameRequest(APIModel):
    practice: bool = False


class AdminSummary(APIModel):
    profiles: int
    active_games: int
    completed_games: int
    active_rooms: int
    pending_review_entries: int


class AdminActionRequest(APIModel):
    reason: str = Field(min_length=3, max_length=300)
    enabled: bool | None = None
    display_name: str | None = Field(default=None, max_length=32)


class FeatureFlagResponse(APIModel):
    key: str
    enabled: bool


class AuditEventResponse(APIModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    target_type: str
    target_id: str
    reason: str | None
    created_at: datetime


class RoomClientMessage(APIModel):
    version: Literal[1]
    type: Literal["guess", "heartbeat"]
    guess: list[str] | None = None
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=80)

    @model_validator(mode="after")
    def validate_guess_event(self) -> RoomClientMessage:
        if self.type == "guess" and (self.guess is None or self.idempotency_key is None):
            raise ValueError("Guess events require a guess and idempotency key.")
        return self


class WebSocketTicketResponse(APIModel):
    ticket: str
    expires_at: datetime


class SupportRequestCreate(APIModel):
    topic: Literal["account", "gameplay", "accessibility", "privacy", "safety", "other"]
    reply_email: str = Field(min_length=3, max_length=254)
    message: str = Field(min_length=10, max_length=4000)

    @field_validator("reply_email")
    @classmethod
    def validate_reply_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[1]:
            raise ValueError("Enter a valid reply email address.")
        if any(ord(character) < 33 for character in normalized):
            raise ValueError("Enter a valid reply email address.")
        return normalized

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if any(character == "\x00" for character in normalized):
            raise ValueError("The message contains an unsupported character.")
        return normalized


class SupportRequestResponse(APIModel):
    id: uuid.UUID
    received: bool


class AdminGameItem(APIModel):
    id: str
    owner_id: uuid.UUID
    mode: str
    status: str
    difficulty: str | None
    attempts_used: int
    max_attempts: int
    score: int | None
    ranked_eligibility: str
    started_at: datetime
    completed_at: datetime | None


class AdminProfileItem(APIModel):
    id: uuid.UUID
    display_name: str | None
    is_anonymous: bool
    public_leaderboards: bool
    is_banned: bool
    deleted_at: datetime | None
    created_at: datetime


class AdminRoomItem(APIModel):
    id: uuid.UUID
    status: str
    member_count: int
    winner_id: uuid.UUID | None
    is_tie: bool
    expires_at: datetime
    created_at: datetime


class AdminChallengeItem(APIModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    title: str | None
    completed_count: int
    revoked_at: datetime | None
    expires_at: datetime
    created_at: datetime


class AdminLeaderboardItem(APIModel):
    id: uuid.UUID
    game_id: uuid.UUID
    user_id: uuid.UUID
    category: str
    score: int
    attempts_used: int
    elapsed_seconds: int
    review_status: str
    invalidated_at: datetime | None
    completed_at: datetime


class AdminPage[AdminItem](APIModel):
    items: list[AdminItem]
    page: int
    page_size: int
    total: int


class ChallengeResultItem(APIModel):
    rank: int = Field(ge=1)
    player_label: str
    result: str
    attempts_used: int
    max_attempts: int
    score: int
    elapsed_seconds: int | None
    completed_at: datetime


class ChallengeResultsResponse(APIModel):
    completed_count: int
    win_rate: float
    average_attempts: float | None
    score_distribution: dict[str, int]
    items: list[ChallengeResultItem]
    page: int
    page_size: int
    total: int
