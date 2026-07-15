from __future__ import annotations

import random
import secrets
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol

from .errors import DomainError
from .feedback import calculate_feedback
from .models import AttemptRecord, GameConfig, GameMode, GameState, GameStatus
from .scoring import calculate_score
from .validation import validate_code


class RandomSource(Protocol):
    def choice(self, sequence: Sequence[str]) -> str: ...

    def sample(self, population: Sequence[str], k: int) -> list[str]: ...


def generate_secret(config: GameConfig, rng: RandomSource | None = None) -> tuple[str, ...]:
    source: RandomSource = rng or secrets.SystemRandom()
    if config.duplicates_allowed:
        return tuple(source.choice(config.colours) for _ in range(config.code_length))
    return tuple(source.sample(config.colours, config.code_length))


def create_game(config: GameConfig, mode: GameMode, *, at: datetime | None = None) -> GameState:
    created = GameState(config=config, mode=mode)
    return created.transition(GameStatus.ACTIVE, at=at)


def submit_guess(
    state: GameState,
    secret: Sequence[str],
    guess: str | Sequence[str],
    *,
    at: datetime | None = None,
    idempotency_key: str | None = None,
) -> GameState:
    if state.status is not GameStatus.ACTIVE:
        raise DomainError("GAME_NOT_ACTIVE", "This game no longer accepts attempts.")
    normalized_secret = validate_code(secret, state.config)
    normalized_guess = validate_code(guess, state.config)
    timestamp = at or datetime.now(UTC)
    feedback = calculate_feedback(normalized_secret, normalized_guess)
    attempt = AttemptRecord(
        number=state.attempts_used + 1,
        guess=normalized_guess,
        feedback=feedback,
        submitted_at=timestamp,
        idempotency_key=idempotency_key,
    )
    attempts = (*state.attempts, attempt)
    target = (
        GameStatus.WON
        if feedback.black == state.config.code_length
        else GameStatus.LOST
        if len(attempts) >= state.config.max_attempts
        else GameStatus.ACTIVE
    )
    completed_at = timestamp if target.terminal else None
    elapsed = max(0.0, (timestamp - (state.started_at or timestamp)).total_seconds())
    score = (
        calculate_score(
            state.config,
            status=target,
            attempts_used=len(attempts),
            elapsed_seconds=elapsed,
        )
        if target.terminal
        else None
    )
    return replace(
        state,
        status=target,
        attempts=attempts,
        completed_at=completed_at,
        score=score,
    )


def abandon_game(state: GameState, *, at: datetime | None = None) -> GameState:
    transitioned = state.transition(GameStatus.ABANDONED, at=at)
    return replace(
        transitioned,
        score=calculate_score(
            state.config,
            status=GameStatus.ABANDONED,
            attempts_used=state.attempts_used,
            elapsed_seconds=0,
        ),
    )


def seeded_rng(seed: int | str | bytes) -> random.Random:
    """Explicit deterministic RNG for tests and documented development tools."""
    return random.Random(seed)
