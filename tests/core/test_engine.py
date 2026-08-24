# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import (
    # Supplies this item to the surrounding call or collection.
    DomainError,
    # Supplies this item to the surrounding call or collection.
    GameConfig,
    # Supplies this item to the surrounding call or collection.
    GameMode,
    # Supplies this item to the surrounding call or collection.
    GameStatus,
    # Supplies this item to the surrounding call or collection.
    abandon_game,
    # Supplies this item to the surrounding call or collection.
    calculate_score,
    # Supplies this item to the surrounding call or collection.
    create_game,
    # Supplies this item to the surrounding call or collection.
    generate_secret,
    # Supplies this item to the surrounding call or collection.
    get_preset,
    # Supplies this item to the surrounding call or collection.
    normalize_code,
    # Supplies this item to the surrounding call or collection.
    seeded_rng,
    # Supplies this item to the surrounding call or collection.
    submit_guess,
    # Supplies this item to the surrounding call or collection.
    validate_code,
    # Closes the multiline call, declaration, or collection started above.
)


# Defines the `test_preset_values` callable and its typed interface.
def test_preset_values() -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert get_preset("easy").to_dict() == {
        # Associates the `colours` key with its value.
        "colours": ["R", "B", "G", "Y", "W"],
        # Associates the `codeLength` key with its value.
        "codeLength": 4,
        # Associates the `maxAttempts` key with its value.
        "maxAttempts": 12,
        # Associates the `duplicatesAllowed` key with its value.
        "duplicatesAllowed": False,
        # Associates the `codeMaker` key with its value.
        "codeMaker": "computer",
        # Associates the `visibility` key with its value.
        "visibility": "private",
        # Associates the `ranked` key with its value.
        "ranked": True,
        # Associates the `timeBonusCap` key with its value.
        "timeBonusCap": 300,
        # Closes the multiline call, declaration, or collection started above.
    }
    # Asserts this invariant so an unexpected test state fails immediately.
    assert get_preset("expert").code_length == 6


# Applies `@pytest.mark.parametrize("value", ["R B G Y", "r,b,g,y", "R-B-G-Y"])` to configure the
# declaration immediately below.
@pytest.mark.parametrize("value", ["R B G Y", "r,b,g,y", "R-B-G-Y"])
# Defines the `test_cli_normalization` callable and its typed interface.
def test_cli_normalization(value: str) -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert normalize_code(value) == ("R", "B", "G", "Y")


# Defines the `test_invalid_guess_does_not_modify_immutable_state` callable and its typed interface.
def test_invalid_guess_does_not_modify_immutable_state() -> None:
    # Computes and stores `state` for subsequent operations.
    state = create_game(get_preset("normal"), GameMode.SOLO)
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError):
        # Calls `submit_guess` with the supplied values.
        submit_guess(state, "RBGY", "R B")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.attempts == ()


# Defines the `test_deterministic_rng_injection` callable and its typed interface.
def test_deterministic_rng_injection() -> None:
    # Computes and stores `config` for subsequent operations.
    config = get_preset("normal")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert generate_secret(config, seeded_rng(4)) == generate_secret(config, seeded_rng(4))


# Defines the `test_no_duplicates_generation` callable and its typed interface.
def test_no_duplicates_generation() -> None:
    # Computes and stores `secret` for subsequent operations.
    secret = generate_secret(get_preset("easy"), seeded_rng(10))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(set(secret)) == len(secret)


# Defines the `test_win_on_final_attempt_and_score` callable and its typed interface.
def test_win_on_final_attempt_and_score() -> None:
    # Computes and stores `config` for subsequent operations.
    config = GameConfig(tuple("RBGYW"), 4, 2, True, ranked=False)
    # Computes and stores `start` for subsequent operations.
    start = datetime(2026, 7, 15, tzinfo=UTC)
    # Computes and stores `state` for subsequent operations.
    state = create_game(config, GameMode.PRACTICE, at=start)
    # Computes and stores `state` for subsequent operations.
    state = submit_guess(state, "RBGY", "RRRR", at=start + timedelta(seconds=10))
    # Computes and stores `state` for subsequent operations.
    state = submit_guess(state, "RBGY", "RBGY", at=start + timedelta(seconds=20))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.status is GameStatus.WON
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.attempts_remaining == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.score is not None and state.score.total > 0


# Defines the `test_attempts_exhausted` callable and its typed interface.
def test_attempts_exhausted() -> None:
    # Computes and stores `config` for subsequent operations.
    config = GameConfig(tuple("RBGYW"), 4, 1, True)
    # Computes and stores `state` for subsequent operations.
    state = submit_guess(create_game(config, GameMode.SOLO), "RBGY", "WWWW")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.status is GameStatus.LOST
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.score is not None and state.score.total == 0
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError, match="no longer accepts"):
        # Calls `submit_guess` with the supplied values.
        submit_guess(state, "RBGY", "RBGY")


# Defines the `test_abandon_is_terminal_and_scores_zero` callable and its typed interface.
def test_abandon_is_terminal_and_scores_zero() -> None:
    # Computes and stores `state` for subsequent operations.
    state = abandon_game(create_game(get_preset("normal"), GameMode.SOLO))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.status is GameStatus.ABANDONED
    # Asserts this invariant so an unexpected test state fails immediately.
    assert state.score is not None and state.score.total == 0


# Defines the `test_illegal_transition_rejected` callable and its typed interface.
def test_illegal_transition_rejected() -> None:
    # Computes and stores `state` for subsequent operations.
    state = create_game(get_preset("normal"), GameMode.SOLO)
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError, match="cannot transition"):
        # Calls `state.transition` with the supplied values.
        state.transition(GameStatus.CREATED)


# Defines the `test_score_ordering_uses_attempts_and_never_elapsed_time` callable and its typed
# interface.
def test_score_ordering_uses_attempts_and_never_elapsed_time() -> None:
    # Computes and stores `config` for subsequent operations.
    config = get_preset("normal")
    # Computes and stores `fast` for subsequent operations.
    fast = calculate_score(config, status=GameStatus.WON, attempts_used=2, elapsed_seconds=5)
    # Computes and stores `equally_fast` for subsequent operations.
    equally_fast = calculate_score(
        # Executes this statement as the next step in the surrounding logic.
        config,
        # Provides the `status` value to the surrounding call.
        status=GameStatus.WON,
        # Provides the `attempts_used` value to the surrounding call.
        attempts_used=6,
        # Provides the `elapsed_seconds` value to the surrounding call.
        elapsed_seconds=5,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `slow` for subsequent operations.
    slow = calculate_score(config, status=GameStatus.WON, attempts_used=6, elapsed_seconds=200)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert fast.total > slow.total >= 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert equally_fast == slow
    # Asserts this invariant so an unexpected test state fails immediately.
    assert fast.time == slow.time == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert fast.version == "score_v1"


# Applies `@pytest.mark.parametrize(` to configure the declaration immediately below.
@pytest.mark.parametrize(
    # Supplies this item to the surrounding call or collection.
    "kwargs",
    # Begins the nested block or multiline expression completed below.
    [
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `colours` key with its value.
            "colours": tuple("RBGY"),
            # Associates the `code_length` key with its value.
            "code_length": 4,
            # Associates the `max_attempts` key with its value.
            "max_attempts": 10,
            # Associates the `duplicates_allowed` key with its value.
            "duplicates_allowed": True,
            # Closes the multiline call, declaration, or collection started above.
        },
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `colours` key with its value.
            "colours": tuple("RBGYW"),
            # Associates the `code_length` key with its value.
            "code_length": 2,
            # Associates the `max_attempts` key with its value.
            "max_attempts": 10,
            # Associates the `duplicates_allowed` key with its value.
            "duplicates_allowed": True,
            # Closes the multiline call, declaration, or collection started above.
        },
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `colours` key with its value.
            "colours": tuple("RBGYW"),
            # Associates the `code_length` key with its value.
            "code_length": 4,
            # Associates the `max_attempts` key with its value.
            "max_attempts": 21,
            # Associates the `duplicates_allowed` key with its value.
            "duplicates_allowed": True,
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    ],
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_custom_boundaries` callable and its typed interface.
def test_custom_boundaries(kwargs: dict[str, object]) -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError):
        # Calls `GameConfig` with the supplied values.
        GameConfig(**kwargs)  # type: ignore[arg-type]


# Defines the `test_duplicates_disabled_validation` callable and its typed interface.
def test_duplicates_disabled_validation() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError, match="does not allow"):
        # Calls `validate_code` with the supplied values.
        validate_code("R R B G", get_preset("easy"))
