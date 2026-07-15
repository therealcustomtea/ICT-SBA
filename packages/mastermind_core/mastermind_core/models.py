from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .errors import DomainError, IllegalTransitionError

COLOUR_IDS = ("R", "B", "G", "Y", "W", "K", "O", "P", "C", "M")
RULE_SET_VERSION = "rules_v1"
SCORING_VERSION = "score_v1"


class GameMode(StrEnum):
    SOLO = "solo"
    DAILY = "daily"
    PRACTICE = "practice"
    PASS_AND_PLAY = "pass_and_play"
    FRIEND_CHALLENGE = "friend_challenge"
    DUEL = "duel"


class GameStatus(StrEnum):
    CREATED = "created"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    ABANDONED = "abandoned"
    EXPIRED = "expired"

    @property
    def terminal(self) -> bool:
        return self in {
            GameStatus.WON,
            GameStatus.LOST,
            GameStatus.ABANDONED,
            GameStatus.EXPIRED,
        }


class GameVisibility(StrEnum):
    PRIVATE = "private"
    SHAREABLE = "shareable"
    PUBLIC = "public"


class CodeMakerType(StrEnum):
    COMPUTER = "computer"
    HUMAN = "human"


class LeaderboardEligibility(StrEnum):
    ELIGIBLE = "eligible"
    UNRANKED = "unranked"
    INVALIDATED = "invalidated"


@dataclass(frozen=True, slots=True)
class GameConfig:
    colours: tuple[str, ...]
    code_length: int
    max_attempts: int
    duplicates_allowed: bool
    code_maker: CodeMakerType = CodeMakerType.COMPUTER
    visibility: GameVisibility = GameVisibility.PRIVATE
    ranked: bool = False
    time_bonus_cap: int = 300

    def __post_init__(self) -> None:
        normalized = tuple(str(colour).strip().upper() for colour in self.colours)
        object.__setattr__(self, "colours", normalized)
        if not 5 <= len(normalized) <= 10:
            raise DomainError("INVALID_COLOUR_COUNT", "Choose between 5 and 10 colours.")
        if len(set(normalized)) != len(normalized):
            raise DomainError("DUPLICATE_COLOUR_OPTION", "Available colours must be unique.")
        if any(colour not in COLOUR_IDS for colour in normalized):
            raise DomainError("UNKNOWN_COLOUR", "The palette contains an unknown colour.")
        if not 3 <= self.code_length <= 6:
            raise DomainError("INVALID_CODE_LENGTH", "Code length must be between 3 and 6.")
        if not 1 <= self.max_attempts <= 20:
            raise DomainError("INVALID_MAX_ATTEMPTS", "Maximum attempts must be between 1 and 20.")
        if not self.duplicates_allowed and len(normalized) < self.code_length:
            raise DomainError(
                "INSUFFICIENT_UNIQUE_COLOURS",
                "Enable at least as many colours as there are code positions.",
            )
        if not 0 <= self.time_bonus_cap <= 3600:
            raise DomainError("INVALID_TIME_BONUS_CAP", "Time bonus cap is out of range.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "colours": list(self.colours),
            "codeLength": self.code_length,
            "maxAttempts": self.max_attempts,
            "duplicatesAllowed": self.duplicates_allowed,
            "codeMaker": self.code_maker.value,
            "visibility": self.visibility.value,
            "ranked": self.ranked,
            "timeBonusCap": self.time_bonus_cap,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> GameConfig:
        return cls(
            colours=tuple(value["colours"]),
            code_length=int(value["codeLength"] if "codeLength" in value else value["code_length"]),
            max_attempts=int(
                value["maxAttempts"] if "maxAttempts" in value else value["max_attempts"]
            ),
            duplicates_allowed=bool(
                value.get("duplicatesAllowed", value.get("duplicates_allowed"))
            ),
            code_maker=CodeMakerType(value.get("codeMaker", value.get("code_maker", "computer"))),
            visibility=GameVisibility(value.get("visibility", "private")),
            ranked=bool(value.get("ranked", False)),
            time_bonus_cap=int(value.get("timeBonusCap", value.get("time_bonus_cap", 300))),
        )


@dataclass(frozen=True, slots=True)
class Feedback:
    black: int
    white: int

    def __post_init__(self) -> None:
        if self.black < 0 or self.white < 0:
            raise DomainError("INVALID_FEEDBACK", "Feedback values cannot be negative.")

    def to_dict(self) -> dict[str, int]:
        return {"black": self.black, "white": self.white}


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    number: int
    guess: tuple[str, ...]
    feedback: Feedback
    submitted_at: datetime
    idempotency_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "guess": list(self.guess),
            "feedback": self.feedback.to_dict(),
            "submittedAt": self.submitted_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    attempts: int
    difficulty: int
    time: int
    total: int
    version: str = SCORING_VERSION

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


ALLOWED_TRANSITIONS: dict[GameStatus, frozenset[GameStatus]] = {
    GameStatus.CREATED: frozenset({GameStatus.ACTIVE}),
    GameStatus.ACTIVE: frozenset(
        {GameStatus.WON, GameStatus.LOST, GameStatus.ABANDONED, GameStatus.EXPIRED}
    ),
    GameStatus.WON: frozenset(),
    GameStatus.LOST: frozenset(),
    GameStatus.ABANDONED: frozenset(),
    GameStatus.EXPIRED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class GameState:
    config: GameConfig
    mode: GameMode
    status: GameStatus = GameStatus.CREATED
    attempts: tuple[AttemptRecord, ...] = field(default_factory=tuple)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    score: ScoreBreakdown | None = None
    rule_set_version: str = RULE_SET_VERSION

    @property
    def attempts_used(self) -> int:
        return len(self.attempts)

    @property
    def attempts_remaining(self) -> int:
        return max(0, self.config.max_attempts - self.attempts_used)

    def transition(self, target: GameStatus, *, at: datetime | None = None) -> GameState:
        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise IllegalTransitionError(self.status.value, target.value)
        timestamp = at or datetime.now(UTC)
        return GameState(
            config=self.config,
            mode=self.mode,
            status=target,
            attempts=self.attempts,
            started_at=timestamp if target is GameStatus.ACTIVE else self.started_at,
            completed_at=timestamp if target.terminal else self.completed_at,
            score=self.score,
            rule_set_version=self.rule_set_version,
        )
