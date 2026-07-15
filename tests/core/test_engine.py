from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from mastermind_core import (
    DomainError,
    GameConfig,
    GameMode,
    GameStatus,
    abandon_game,
    calculate_score,
    create_game,
    generate_secret,
    get_preset,
    normalize_code,
    seeded_rng,
    submit_guess,
    validate_code,
)


def test_preset_values() -> None:
    assert get_preset("easy").to_dict() == {
        "colours": ["R", "B", "G", "Y", "W"],
        "codeLength": 4,
        "maxAttempts": 12,
        "duplicatesAllowed": False,
        "codeMaker": "computer",
        "visibility": "private",
        "ranked": True,
        "timeBonusCap": 300,
    }
    assert get_preset("expert").code_length == 6


@pytest.mark.parametrize("value", ["R B G Y", "r,b,g,y", "R-B-G-Y"])
def test_cli_normalization(value: str) -> None:
    assert normalize_code(value) == ("R", "B", "G", "Y")


def test_invalid_guess_does_not_modify_immutable_state() -> None:
    state = create_game(get_preset("normal"), GameMode.SOLO)
    with pytest.raises(DomainError):
        submit_guess(state, "RBGY", "R B")
    assert state.attempts == ()


def test_deterministic_rng_injection() -> None:
    config = get_preset("normal")
    assert generate_secret(config, seeded_rng(4)) == generate_secret(config, seeded_rng(4))


def test_no_duplicates_generation() -> None:
    secret = generate_secret(get_preset("easy"), seeded_rng(10))
    assert len(set(secret)) == len(secret)


def test_win_on_final_attempt_and_score() -> None:
    config = GameConfig(tuple("RBGYW"), 4, 2, True, ranked=False)
    start = datetime(2026, 7, 15, tzinfo=UTC)
    state = create_game(config, GameMode.PRACTICE, at=start)
    state = submit_guess(state, "RBGY", "RRRR", at=start + timedelta(seconds=10))
    state = submit_guess(state, "RBGY", "RBGY", at=start + timedelta(seconds=20))
    assert state.status is GameStatus.WON
    assert state.attempts_remaining == 0
    assert state.score is not None and state.score.total > 0


def test_attempts_exhausted() -> None:
    config = GameConfig(tuple("RBGYW"), 4, 1, True)
    state = submit_guess(create_game(config, GameMode.SOLO), "RBGY", "WWWW")
    assert state.status is GameStatus.LOST
    assert state.score is not None and state.score.total == 0
    with pytest.raises(DomainError, match="no longer accepts"):
        submit_guess(state, "RBGY", "RBGY")


def test_abandon_is_terminal_and_scores_zero() -> None:
    state = abandon_game(create_game(get_preset("normal"), GameMode.SOLO))
    assert state.status is GameStatus.ABANDONED
    assert state.score is not None and state.score.total == 0


def test_illegal_transition_rejected() -> None:
    state = create_game(get_preset("normal"), GameMode.SOLO)
    with pytest.raises(DomainError, match="cannot transition"):
        state.transition(GameStatus.CREATED)


def test_score_ordering_uses_attempts_and_never_elapsed_time() -> None:
    config = get_preset("normal")
    fast = calculate_score(config, status=GameStatus.WON, attempts_used=2, elapsed_seconds=5)
    equally_fast = calculate_score(
        config, status=GameStatus.WON, attempts_used=6, elapsed_seconds=5
    )
    slow = calculate_score(config, status=GameStatus.WON, attempts_used=6, elapsed_seconds=200)
    assert fast.total > slow.total >= 0
    assert equally_fast == slow
    assert fast.time == slow.time == 0
    assert fast.version == "score_v1"


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "colours": tuple("RBGY"),
            "code_length": 4,
            "max_attempts": 10,
            "duplicates_allowed": True,
        },
        {
            "colours": tuple("RBGYW"),
            "code_length": 2,
            "max_attempts": 10,
            "duplicates_allowed": True,
        },
        {
            "colours": tuple("RBGYW"),
            "code_length": 4,
            "max_attempts": 21,
            "duplicates_allowed": True,
        },
    ],
)
def test_custom_boundaries(kwargs: dict[str, object]) -> None:
    with pytest.raises(DomainError):
        GameConfig(**kwargs)  # type: ignore[arg-type]


def test_duplicates_disabled_validation() -> None:
    with pytest.raises(DomainError, match="does not allow"):
        validate_code("R R B G", get_preset("easy"))
