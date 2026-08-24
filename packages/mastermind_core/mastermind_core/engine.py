# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports `random` so its functionality is available below.
import random

# Imports `secrets` so its functionality is available below.
import secrets

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Sequence

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import replace

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime

# Imports selected names from `typing` for use in this module.
from typing import Protocol

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError

# Imports selected names from `.feedback` for use in this module.
from .feedback import calculate_feedback

# Imports selected names from `.models` for use in this module.
from .models import AttemptRecord, GameConfig, GameMode, GameState, GameStatus

# Imports selected names from `.scoring` for use in this module.
from .scoring import calculate_score

# Imports selected names from `.validation` for use in this module.
from .validation import validate_code


# Defines `RandomSource` as a specialization of `Protocol`.
class RandomSource(Protocol):
    # Defines the `choice` function and begins its typed parameter list.
    def choice(self, sequence: Sequence[str]) -> str: ...

    # Defines the `sample` function and begins its typed parameter list.
    def sample(self, population: Sequence[str], k: int) -> list[str]: ...


# Defines the `generate_secret` function and begins its typed parameter list.
def generate_secret(config: GameConfig, rng: RandomSource | None = None) -> tuple[str, ...]:
    # Computes `rng or secrets.SystemRandom()` and stores the result in `source` for later use.
    source: RandomSource = rng or secrets.SystemRandom()
    # Tests `config.duplicates_allowed` before running the nested branch.
    if config.duplicates_allowed:
        # Returns `tuple(source.choice(config.colours) for _ in range(config.code_length))` to
        # the caller as this function's result.
        return tuple(source.choice(config.colours) for _ in range(config.code_length))
    # Returns `tuple(source.sample(config.colours, config.code_length))` to the caller as this
    # function's result.
    return tuple(source.sample(config.colours, config.code_length))


# Defines the `create_game` function and begins its typed parameter list.
def create_game(config: GameConfig, mode: GameMode, *, at: datetime | None = None) -> GameState:
    # Computes `GameState(config=config, mode=mode)` and stores the result in `created` for
    # later use.
    created = GameState(config=config, mode=mode)
    # Returns `created.transition(GameStatus.ACTIVE, at=at)` to the caller as this function's
    # result.
    return created.transition(GameStatus.ACTIVE, at=at)


# Defines the `submit_guess` function and begins its typed parameter list.
def submit_guess(
    # Declares `state` as `GameState,` so the data shape is explicit.
    state: GameState,
    # Declares `secret` as `Sequence[str],` so the data shape is explicit.
    secret: Sequence[str],
    # Declares `guess` as `str | Sequence[str],` so the data shape is explicit.
    guess: str | Sequence[str],
    # Makes all following function parameters keyword-only for clearer call sites.
    *,
    # Provides `None` as the `at` parameter or argument.
    at: datetime | None = None,
    # Provides `None` as the `idempotency_key` parameter or argument.
    idempotency_key: str | None = None,
    # Completes the function signature and declares the type returned to callers.
) -> GameState:
    # Tests `state.status is not GameStatus.ACTIVE` before running the nested branch.
    if state.status is not GameStatus.ACTIVE:
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError("GAME_NOT_ACTIVE", "This game no longer accepts attempts.")
    # Computes `validate_code(secret, state.config)` and stores the result in
    # `normalized_secret` for later use.
    normalized_secret = validate_code(secret, state.config)
    # Computes `validate_code(guess, state.config)` and stores the result in `normalized_guess`
    # for later use.
    normalized_guess = validate_code(guess, state.config)
    # Computes `at or datetime.now(UTC)` and stores the result in `timestamp` for later use.
    timestamp = at or datetime.now(UTC)
    # Computes `calculate_feedback(normalized_secret, normalized_guess)` and stores the result
    # in `feedback` for later use.
    feedback = calculate_feedback(normalized_secret, normalized_guess)
    # Computes `AttemptRecord(` and stores the result in `attempt` for later use.
    attempt = AttemptRecord(
        # Provides `state.attempts_used + 1` as the `number` parameter or argument.
        number=state.attempts_used + 1,
        # Provides `normalized_guess` as the `guess` parameter or argument.
        guess=normalized_guess,
        # Provides `feedback` as the `feedback` parameter or argument.
        feedback=feedback,
        # Provides `timestamp` as the `submitted_at` parameter or argument.
        submitted_at=timestamp,
        # Provides `idempotency_key` as the `idempotency_key` parameter or argument.
        idempotency_key=idempotency_key,
        # Closes the multiline call or collection started on an earlier line.
    )
    # Computes `(*state.attempts, attempt)` and stores the result in `attempts` for later use.
    attempts = (*state.attempts, attempt)
    # Computes `(` and stores the result in `target` for later use.
    target = (
        # Continues the surrounding expression or executes the next required operation.
        GameStatus.WON
        # Tests `feedback.black == state.config.code_length` before running the nested branch.
        if feedback.black == state.config.code_length
        # Continues the surrounding expression or executes the next required operation.
        else GameStatus.LOST
        # Tests `len(attempts) >= state.config.max_attempts` before running the nested branch.
        if len(attempts) >= state.config.max_attempts
        # Continues the surrounding expression or executes the next required operation.
        else GameStatus.ACTIVE
        # Closes the multiline call or collection started on an earlier line.
    )
    # Computes `timestamp if target.terminal else None` and stores the result in `completed_at`
    # for later use.
    completed_at = timestamp if target.terminal else None
    # Computes `max(0.0, (timestamp - (state.started_at or timestamp)).total_seconds())` and
    # stores the result in `elapsed` for later use.
    elapsed = max(0.0, (timestamp - (state.started_at or timestamp)).total_seconds())
    # Computes `(` and stores the result in `score` for later use.
    score = (
        # Starts a multiline function call whose arguments are supplied below.
        calculate_score(
            # Supplies this value to the surrounding multiline call or collection.
            state.config,
            # Provides `target` as the `status` parameter or argument.
            status=target,
            # Provides `len(attempts)` as the `attempts_used` parameter or argument.
            attempts_used=len(attempts),
            # Provides `elapsed` as the `elapsed_seconds` parameter or argument.
            elapsed_seconds=elapsed,
            # Closes the multiline call or collection started on an earlier line.
        )
        # Tests `target.terminal` before running the nested branch.
        if target.terminal
        # Continues the surrounding expression or executes the next required operation.
        else None
        # Closes the multiline call or collection started on an earlier line.
    )
    # Begins constructing the value that this function returns to its caller.
    return replace(
        # Includes `state` in the surrounding import, call, or collection.
        state,
        # Provides `target` as the `status` parameter or argument.
        status=target,
        # Provides `attempts` as the `attempts` parameter or argument.
        attempts=attempts,
        # Provides `completed_at` as the `completed_at` parameter or argument.
        completed_at=completed_at,
        # Provides `score` as the `score` parameter or argument.
        score=score,
        # Closes the multiline call or collection started on an earlier line.
    )


# Defines the `abandon_game` function and begins its typed parameter list.
def abandon_game(state: GameState, *, at: datetime | None = None) -> GameState:
    # Computes `state.transition(GameStatus.ABANDONED, at=at)` and stores the result in
    # `transitioned` for later use.
    transitioned = state.transition(GameStatus.ABANDONED, at=at)
    # Begins constructing the value that this function returns to its caller.
    return replace(
        # Includes `transitioned` in the surrounding import, call, or collection.
        transitioned,
        # Computes `calculate_score(` and stores the result in `score` for later use.
        score=calculate_score(
            # Supplies this value to the surrounding multiline call or collection.
            state.config,
            # Provides `GameStatus.ABANDONED` as the `status` parameter or argument.
            status=GameStatus.ABANDONED,
            # Provides `state.attempts_used` as the `attempts_used` parameter or argument.
            attempts_used=state.attempts_used,
            # Provides `0` as the `elapsed_seconds` parameter or argument.
            elapsed_seconds=0,
            # Closes the multiline call or collection started on an earlier line.
        ),
        # Closes the multiline call or collection started on an earlier line.
    )


# Defines the `seeded_rng` function and begins its typed parameter list.
def seeded_rng(seed: int | str | bytes) -> random.Random:
    # Adds the `Explicit deterministic RNG for tests and documented development tools.` string
    # to the surrounding call or ordered collection.
    """Explicit deterministic RNG for tests and documented development tools."""
    # Returns `random.Random(seed)` to the caller as this function's result.
    return random.Random(seed)
