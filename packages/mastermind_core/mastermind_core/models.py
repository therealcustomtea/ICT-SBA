# ruff: noqa: I001 -- line explanations intentionally separate imports.
# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import asdict, dataclass, field
# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime
# Imports selected names from `enum` for use in this module.
from enum import StrEnum
# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError, IllegalTransitionError

# Assigns `("R", "B", "G", "Y", "W", "K", "O", "P", "C", "M")` to the named `COLOUR_IDS`
# constant used by the application.
COLOUR_IDS = ("R", "B", "G", "Y", "W", "K", "O", "P", "C", "M")
# Assigns `"rules_v1"` to the named `RULE_SET_VERSION` constant used by the application.
RULE_SET_VERSION = "rules_v1"
# Assigns `"score_v1"` to the named `SCORING_VERSION` constant used by the application.
SCORING_VERSION = "score_v1"


# Defines `GameMode` as a specialization of `StrEnum`.
class GameMode(StrEnum):
    # Assigns `"solo"` to the named `SOLO` constant used by the application.
    SOLO = "solo"
    # Assigns `"daily"` to the named `DAILY` constant used by the application.
    DAILY = "daily"
    # Assigns `"practice"` to the named `PRACTICE` constant used by the application.
    PRACTICE = "practice"
    # Assigns `"pass_and_play"` to the named `PASS_AND_PLAY` constant used by the application.
    PASS_AND_PLAY = "pass_and_play"
    # Assigns `"friend_challenge"` to the named `FRIEND_CHALLENGE` constant used by the
    # application.
    FRIEND_CHALLENGE = "friend_challenge"
    # Assigns `"duel"` to the named `DUEL` constant used by the application.
    DUEL = "duel"


# Defines `GameStatus` as a specialization of `StrEnum`.
class GameStatus(StrEnum):
    # Assigns `"created"` to the named `CREATED` constant used by the application.
    CREATED = "created"
    # Assigns `"active"` to the named `ACTIVE` constant used by the application.
    ACTIVE = "active"
    # Assigns `"won"` to the named `WON` constant used by the application.
    WON = "won"
    # Assigns `"lost"` to the named `LOST` constant used by the application.
    LOST = "lost"
    # Assigns `"abandoned"` to the named `ABANDONED` constant used by the application.
    ABANDONED = "abandoned"
    # Assigns `"expired"` to the named `EXPIRED` constant used by the application.
    EXPIRED = "expired"

    # Applies `@property` to configure the class or method declared immediately below.
    @property
    # Defines the `terminal` function and begins its typed parameter list.
    def terminal(self) -> bool:
        # Begins constructing the value that this function returns to its caller.
        return self in {
            # Supplies this value to the surrounding multiline call or collection.
            GameStatus.WON,
            # Supplies this value to the surrounding multiline call or collection.
            GameStatus.LOST,
            # Supplies this value to the surrounding multiline call or collection.
            GameStatus.ABANDONED,
            # Supplies this value to the surrounding multiline call or collection.
            GameStatus.EXPIRED,
        # Closes the multiline call or collection started on an earlier line.
        }


# Defines `GameVisibility` as a specialization of `StrEnum`.
class GameVisibility(StrEnum):
    # Assigns `"private"` to the named `PRIVATE` constant used by the application.
    PRIVATE = "private"
    # Assigns `"shareable"` to the named `SHAREABLE` constant used by the application.
    SHAREABLE = "shareable"
    # Assigns `"public"` to the named `PUBLIC` constant used by the application.
    PUBLIC = "public"


# Defines `CodeMakerType` as a specialization of `StrEnum`.
class CodeMakerType(StrEnum):
    # Assigns `"computer"` to the named `COMPUTER` constant used by the application.
    COMPUTER = "computer"
    # Assigns `"human"` to the named `HUMAN` constant used by the application.
    HUMAN = "human"


# Defines `LeaderboardEligibility` as a specialization of `StrEnum`.
class LeaderboardEligibility(StrEnum):
    # Assigns `"eligible"` to the named `ELIGIBLE` constant used by the application.
    ELIGIBLE = "eligible"
    # Assigns `"unranked"` to the named `UNRANKED` constant used by the application.
    UNRANKED = "unranked"
    # Assigns `"invalidated"` to the named `INVALIDATED` constant used by the application.
    INVALIDATED = "invalidated"


# Applies `@dataclass(frozen=True, slots=True)` to configure the class or method declared
# immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `GameConfig` type used to group related data and behavior.
class GameConfig:
    # Declares `colours` as `tuple[str, ...]` so the data shape is explicit.
    colours: tuple[str, ...]
    # Declares `code_length` as `int` so the data shape is explicit.
    code_length: int
    # Declares `max_attempts` as `int` so the data shape is explicit.
    max_attempts: int
    # Declares `duplicates_allowed` as `bool` so the data shape is explicit.
    duplicates_allowed: bool
    # Computes `CodeMakerType.COMPUTER` and stores the result in `code_maker` for later use.
    code_maker: CodeMakerType = CodeMakerType.COMPUTER
    # Computes `GameVisibility.PRIVATE` and stores the result in `visibility` for later use.
    visibility: GameVisibility = GameVisibility.PRIVATE
    # Computes `False` and stores the result in `ranked` for later use.
    ranked: bool = False
    # Computes `300` and stores the result in `time_bonus_cap` for later use.
    time_bonus_cap: int = 300

    # Defines the `__post_init__` function and begins its typed parameter list.
    def __post_init__(self) -> None:
        # Computes `tuple(str(colour).strip().upper() for colour in self.colours)` and stores
        # the result in `normalized` for later use.
        normalized = tuple(str(colour).strip().upper() for colour in self.colours)
        # Assigns the normalized value inside this otherwise frozen data class.
        object.__setattr__(self, "colours", normalized)
        # Tests `not 5 <= len(normalized) <= 10` before running the nested branch.
        if not 5 <= len(normalized) <= 10:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("INVALID_COLOUR_COUNT", "Choose between 5 and 10 colours.")
        # Tests `len(set(normalized)) != len(normalized)` before running the nested branch.
        if len(set(normalized)) != len(normalized):
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("DUPLICATE_COLOUR_OPTION", "Available colours must be unique.")
        # Tests `any(colour not in COLOUR_IDS for colour in normalized)` before running the
        # nested branch.
        if any(colour not in COLOUR_IDS for colour in normalized):
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("UNKNOWN_COLOUR", "The palette contains an unknown colour.")
        # Tests `not 3 <= self.code_length <= 6` before running the nested branch.
        if not 3 <= self.code_length <= 6:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("INVALID_CODE_LENGTH", "Code length must be between 3 and 6.")
        # Tests `not 1 <= self.max_attempts <= 20` before running the nested branch.
        if not 1 <= self.max_attempts <= 20:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("INVALID_MAX_ATTEMPTS", "Maximum attempts must be between 1 and 20.")
        # Tests `not self.duplicates_allowed and len(normalized) < self.code_length` before
        # running the nested branch.
        if not self.duplicates_allowed and len(normalized) < self.code_length:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError(
                # Adds the `INSUFFICIENT_UNIQUE_COLOURS` string to the surrounding call or
                # ordered collection.
                "INSUFFICIENT_UNIQUE_COLOURS",
                # Adds the `Enable at least as many colours as there are code positions.` string
                # to the surrounding call or ordered collection.
                "Enable at least as many colours as there are code positions.",
            # Closes the multiline call or collection started on an earlier line.
            )
        # Tests `not 0 <= self.time_bonus_cap <= 3600` before running the nested branch.
        if not 0 <= self.time_bonus_cap <= 3600:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("INVALID_TIME_BONUS_CAP", "Time bonus cap is out of range.")

    # Defines the `to_dict` function and begins its typed parameter list.
    def to_dict(self) -> dict[str, Any]:
        # Begins constructing the value that this function returns to its caller.
        return {
            # Maps the `colours` field to `list(self.colours)` in the dictionary.
            "colours": list(self.colours),
            # Maps the `codeLength` field to `self.code_length` in the dictionary.
            "codeLength": self.code_length,
            # Maps the `maxAttempts` field to `self.max_attempts` in the dictionary.
            "maxAttempts": self.max_attempts,
            # Maps the `duplicatesAllowed` field to `self.duplicates_allowed` in the dictionary.
            "duplicatesAllowed": self.duplicates_allowed,
            # Maps the `codeMaker` field to `self.code_maker.value` in the dictionary.
            "codeMaker": self.code_maker.value,
            # Maps the `visibility` field to `self.visibility.value` in the dictionary.
            "visibility": self.visibility.value,
            # Maps the `ranked` field to `self.ranked` in the dictionary.
            "ranked": self.ranked,
            # Maps the `timeBonusCap` field to `self.time_bonus_cap` in the dictionary.
            "timeBonusCap": self.time_bonus_cap,
        # Closes the multiline call or collection started on an earlier line.
        }

    # Applies `@classmethod` to configure the class or method declared immediately below.
    @classmethod
    # Defines the `from_dict` function and begins its typed parameter list.
    def from_dict(cls, value: dict[str, Any]) -> GameConfig:
        # Begins constructing the value that this function returns to its caller.
        return cls(
            # Provides `tuple(value["colours"])` as the `colours` parameter or argument.
            colours=tuple(value["colours"]),
            # Provides `int(value["codeLength"] if "codeLength" in value else
            # value["code_length"])` as the `code_length` parameter or argument.
            code_length=int(value["codeLength"] if "codeLength" in value else value["code_length"]),
            # Computes `int(` and stores the result in `max_attempts` for later use.
            max_attempts=int(
                # Continues the surrounding expression or executes the next required operation.
                value["maxAttempts"] if "maxAttempts" in value else value["max_attempts"]
            # Closes the multiline call or collection started on an earlier line.
            ),
            # Computes `bool(` and stores the result in `duplicates_allowed` for later use.
            duplicates_allowed=bool(
                # Calls `value.get` to perform this step with the supplied arguments.
                value.get("duplicatesAllowed", value.get("duplicates_allowed"))
            # Closes the multiline call or collection started on an earlier line.
            ),
            # Provides `CodeMakerType(value.get("codeMaker", value.get("code_maker",
            # "computer")))` as the `code_maker` parameter or argument.
            code_maker=CodeMakerType(value.get("codeMaker", value.get("code_maker", "computer"))),
            # Provides `GameVisibility(value.get("visibility", "private"))` as the `visibility`
            # parameter or argument.
            visibility=GameVisibility(value.get("visibility", "private")),
            # Provides `bool(value.get("ranked", False))` as the `ranked` parameter or argument.
            ranked=bool(value.get("ranked", False)),
            # Provides `int(value.get("timeBonusCap", value.get("time_bonus_cap", 300)))` as the
            # `time_bonus_cap` parameter or argument.
            time_bonus_cap=int(value.get("timeBonusCap", value.get("time_bonus_cap", 300))),
        # Closes the multiline call or collection started on an earlier line.
        )


# Applies `@dataclass(frozen=True, slots=True)` to configure the class or method declared
# immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `Feedback` type used to group related data and behavior.
class Feedback:
    # Declares `black` as `int` so the data shape is explicit.
    black: int
    # Declares `white` as `int` so the data shape is explicit.
    white: int

    # Defines the `__post_init__` function and begins its typed parameter list.
    def __post_init__(self) -> None:
        # Tests `self.black < 0 or self.white < 0` before running the nested branch.
        if self.black < 0 or self.white < 0:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("INVALID_FEEDBACK", "Feedback values cannot be negative.")

    # Defines the `to_dict` function and begins its typed parameter list.
    def to_dict(self) -> dict[str, int]:
        # Returns `{"black": self.black, "white": self.white}` to the caller as this function's
        # result.
        return {"black": self.black, "white": self.white}


# Applies `@dataclass(frozen=True, slots=True)` to configure the class or method declared
# immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `AttemptRecord` type used to group related data and behavior.
class AttemptRecord:
    # Declares `number` as `int` so the data shape is explicit.
    number: int
    # Declares `guess` as `tuple[str, ...]` so the data shape is explicit.
    guess: tuple[str, ...]
    # Declares `feedback` as `Feedback` so the data shape is explicit.
    feedback: Feedback
    # Declares `submitted_at` as `datetime` so the data shape is explicit.
    submitted_at: datetime
    # Computes `None` and stores the result in `idempotency_key` for later use.
    idempotency_key: str | None = None

    # Defines the `to_dict` function and begins its typed parameter list.
    def to_dict(self) -> dict[str, Any]:
        # Begins constructing the value that this function returns to its caller.
        return {
            # Maps the `number` field to `self.number` in the dictionary.
            "number": self.number,
            # Maps the `guess` field to `list(self.guess)` in the dictionary.
            "guess": list(self.guess),
            # Maps the `feedback` field to `self.feedback.to_dict()` in the dictionary.
            "feedback": self.feedback.to_dict(),
            # Maps the `submittedAt` field to `self.submitted_at.isoformat()` in the dictionary.
            "submittedAt": self.submitted_at.isoformat(),
        # Closes the multiline call or collection started on an earlier line.
        }


# Applies `@dataclass(frozen=True, slots=True)` to configure the class or method declared
# immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `ScoreBreakdown` type used to group related data and behavior.
class ScoreBreakdown:
    # Declares `attempts` as `int` so the data shape is explicit.
    attempts: int
    # Declares `difficulty` as `int` so the data shape is explicit.
    difficulty: int
    # Declares `time` as `int` so the data shape is explicit.
    time: int
    # Declares `total` as `int` so the data shape is explicit.
    total: int
    # Computes `SCORING_VERSION` and stores the result in `version` for later use.
    version: str = SCORING_VERSION

    # Defines the `to_dict` function and begins its typed parameter list.
    def to_dict(self) -> dict[str, int | str]:
        # Returns `asdict(self)` to the caller as this function's result.
        return asdict(self)


# Assigns `{` to the named `ALLOWED_TRANSITIONS` constant used by the application.
ALLOWED_TRANSITIONS: dict[GameStatus, frozenset[GameStatus]] = {
    # Supplies this value to the surrounding multiline call or collection.
    GameStatus.CREATED: frozenset({GameStatus.ACTIVE}),
    # Starts a multiline function call whose arguments are supplied below.
    GameStatus.ACTIVE: frozenset(
        # Continues the surrounding expression or executes the next required operation.
        {GameStatus.WON, GameStatus.LOST, GameStatus.ABANDONED, GameStatus.EXPIRED}
    # Closes the multiline call or collection started on an earlier line.
    ),
    # Supplies this value to the surrounding multiline call or collection.
    GameStatus.WON: frozenset(),
    # Supplies this value to the surrounding multiline call or collection.
    GameStatus.LOST: frozenset(),
    # Supplies this value to the surrounding multiline call or collection.
    GameStatus.ABANDONED: frozenset(),
    # Supplies this value to the surrounding multiline call or collection.
    GameStatus.EXPIRED: frozenset(),
# Closes the multiline call or collection started on an earlier line.
}


# Applies `@dataclass(frozen=True, slots=True)` to configure the class or method declared
# immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `GameState` type used to group related data and behavior.
class GameState:
    # Declares `config` as `GameConfig` so the data shape is explicit.
    config: GameConfig
    # Declares `mode` as `GameMode` so the data shape is explicit.
    mode: GameMode
    # Computes `GameStatus.CREATED` and stores the result in `status` for later use.
    status: GameStatus = GameStatus.CREATED
    # Computes `field(default_factory=tuple)` and stores the result in `attempts` for later use.
    attempts: tuple[AttemptRecord, ...] = field(default_factory=tuple)
    # Computes `None` and stores the result in `started_at` for later use.
    started_at: datetime | None = None
    # Computes `None` and stores the result in `completed_at` for later use.
    completed_at: datetime | None = None
    # Computes `None` and stores the result in `score` for later use.
    score: ScoreBreakdown | None = None
    # Computes `RULE_SET_VERSION` and stores the result in `rule_set_version` for later use.
    rule_set_version: str = RULE_SET_VERSION

    # Applies `@property` to configure the class or method declared immediately below.
    @property
    # Defines the `attempts_used` function and begins its typed parameter list.
    def attempts_used(self) -> int:
        # Returns `len(self.attempts)` to the caller as this function's result.
        return len(self.attempts)

    # Applies `@property` to configure the class or method declared immediately below.
    @property
    # Defines the `attempts_remaining` function and begins its typed parameter list.
    def attempts_remaining(self) -> int:
        # Returns `max(0, self.config.max_attempts - self.attempts_used)` to the caller as this
        # function's result.
        return max(0, self.config.max_attempts - self.attempts_used)

    # Defines the `transition` function and begins its typed parameter list.
    def transition(self, target: GameStatus, *, at: datetime | None = None) -> GameState:
        # Tests `target not in ALLOWED_TRANSITIONS[self.status]` before running the nested
        # branch.
        if target not in ALLOWED_TRANSITIONS[self.status]:
            # Raises the specified exception to report an invalid or failed operation.
            raise IllegalTransitionError(self.status.value, target.value)
        # Computes `at or datetime.now(UTC)` and stores the result in `timestamp` for later use.
        timestamp = at or datetime.now(UTC)
        # Begins constructing the value that this function returns to its caller.
        return GameState(
            # Provides `self.config` as the `config` parameter or argument.
            config=self.config,
            # Provides `self.mode` as the `mode` parameter or argument.
            mode=self.mode,
            # Provides `target` as the `status` parameter or argument.
            status=target,
            # Provides `self.attempts` as the `attempts` parameter or argument.
            attempts=self.attempts,
            # Provides `timestamp if target is GameStatus.ACTIVE else self.started_at` as the
            # `started_at` parameter or argument.
            started_at=timestamp if target is GameStatus.ACTIVE else self.started_at,
            # Provides `timestamp if target.terminal else self.completed_at` as the
            # `completed_at` parameter or argument.
            completed_at=timestamp if target.terminal else self.completed_at,
            # Provides `self.score` as the `score` parameter or argument.
            score=self.score,
            # Provides `self.rule_set_version` as the `rule_set_version` parameter or argument.
            rule_set_version=self.rule_set_version,
        # Closes the multiline call or collection started on an earlier line.
        )
