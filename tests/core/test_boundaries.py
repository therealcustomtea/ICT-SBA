# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `hmac` so the module can use that dependency.
import hmac

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, date, datetime

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import (
    # Supplies this item to the surrounding call or collection.
    AttemptRecord,
    # Supplies this item to the surrounding call or collection.
    DomainError,
    # Supplies this item to the surrounding call or collection.
    Feedback,
    # Supplies this item to the surrounding call or collection.
    GameConfig,
    # Supplies this item to the surrounding call or collection.
    GameStatus,
    # Supplies this item to the surrounding call or collection.
    ScoreBreakdown,
    # Supplies this item to the surrounding call or collection.
    derive_daily_secret,
    # Supplies this item to the surrounding call or collection.
    get_preset,
    # Supplies this item to the surrounding call or collection.
    normalize_code,
    # Supplies this item to the surrounding call or collection.
    preset_name,
    # Supplies this item to the surrounding call or collection.
    validate_code,
    # Closes the multiline call, declaration, or collection started above.
)


# Applies `@pytest.mark.parametrize(` to configure the declaration immediately below.
@pytest.mark.parametrize(
    # Supplies this item to the surrounding call or collection.
    ("kwargs", "code"),
    # Begins the nested block or multiline expression completed below.
    [
        # Begins the nested block or multiline expression completed below.
        (
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `colours` key with its value.
                "colours": tuple("RBGYR"),
                # Associates the `code_length` key with its value.
                "code_length": 4,
                # Associates the `max_attempts` key with its value.
                "max_attempts": 10,
                # Associates the `duplicates_allowed` key with its value.
                "duplicates_allowed": True,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Supplies this item to the surrounding call or collection.
            "DUPLICATE_COLOUR_OPTION",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Begins the nested block or multiline expression completed below.
        (
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `colours` key with its value.
                "colours": ("R", "B", "G", "Y", "Z"),
                # Associates the `code_length` key with its value.
                "code_length": 4,
                # Associates the `max_attempts` key with its value.
                "max_attempts": 10,
                # Associates the `duplicates_allowed` key with its value.
                "duplicates_allowed": True,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Supplies this item to the surrounding call or collection.
            "UNKNOWN_COLOUR",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Begins the nested block or multiline expression completed below.
        (
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `colours` key with its value.
                "colours": tuple("RBGYW"),
                # Associates the `code_length` key with its value.
                "code_length": 6,
                # Associates the `max_attempts` key with its value.
                "max_attempts": 10,
                # Associates the `duplicates_allowed` key with its value.
                "duplicates_allowed": False,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Supplies this item to the surrounding call or collection.
            "INSUFFICIENT_UNIQUE_COLOURS",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Begins the nested block or multiline expression completed below.
        (
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `colours` key with its value.
                "colours": tuple("RBGYW"),
                # Associates the `code_length` key with its value.
                "code_length": 4,
                # Associates the `max_attempts` key with its value.
                "max_attempts": 10,
                # Associates the `duplicates_allowed` key with its value.
                "duplicates_allowed": True,
                # Associates the `time_bonus_cap` key with its value.
                "time_bonus_cap": 3601,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Supplies this item to the surrounding call or collection.
            "INVALID_TIME_BONUS_CAP",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    ],
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_configuration_rejects_each_invalid_boundary` callable and its typed interface.
def test_configuration_rejects_each_invalid_boundary(kwargs: dict[str, object], code: str) -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError) as error:
        # Calls `GameConfig` with the supplied values.
        GameConfig(**kwargs)  # type: ignore[arg-type]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == code


# Defines the `test_snake_case_config_deserialization_and_value_serializers` callable and its typed
# interface.
def test_snake_case_config_deserialization_and_value_serializers() -> None:
    # Computes and stores `config` for subsequent operations.
    config = GameConfig.from_dict(
        # Begins the nested block or multiline expression completed below.
        {
            # Associates the `colours` key with its value.
            "colours": list("RBGYW"),
            # Associates the `code_length` key with its value.
            "code_length": 4,
            # Associates the `max_attempts` key with its value.
            "max_attempts": 9,
            # Associates the `duplicates_allowed` key with its value.
            "duplicates_allowed": True,
            # Associates the `code_maker` key with its value.
            "code_maker": "computer",
            # Associates the `time_bonus_cap` key with its value.
            "time_bonus_cap": 60,
            # Closes the multiline call, declaration, or collection started above.
        }
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert config.max_attempts == 9
    # Computes and stores `feedback` for subsequent operations.
    feedback = Feedback(black=1, white=2)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert feedback.to_dict() == {"black": 1, "white": 2}
    # Computes and stores `attempt` for subsequent operations.
    attempt = AttemptRecord(
        # Provides the `number` parameter or keyword argument.
        number=1,
        # Provides the `guess` parameter or keyword argument.
        guess=("R", "B", "G", "Y"),
        # Provides the `feedback` parameter or keyword argument.
        feedback=feedback,
        # Provides the `submitted_at` parameter or keyword argument.
        submitted_at=datetime(2026, 7, 15, tzinfo=UTC),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert attempt.to_dict()["submittedAt"] == "2026-07-15T00:00:00+00:00"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert ScoreBreakdown(100, 200, 30, 330).to_dict()["version"] == "score_v1"


# Defines the `test_negative_feedback_is_rejected` callable and its typed interface.
def test_negative_feedback_is_rejected() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError) as error:
        # Calls `Feedback` with the supplied values.
        Feedback(-1, 0)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == "INVALID_FEEDBACK"


# Defines the `test_preset_lookup_name_and_unknown_paths` callable and its typed interface.
def test_preset_lookup_name_and_unknown_paths() -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert get_preset(" EASY ") == get_preset("easy")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert preset_name(get_preset("hard")) == "hard"
    # Computes and stores `custom` for subsequent operations.
    custom = GameConfig(tuple("RBGYW"), 3, 7, True)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert preset_name(custom) is None
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError) as error:
        # Calls `get_preset` with the supplied values.
        get_preset("impossible")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == "UNKNOWN_DIFFICULTY"


# Applies `@pytest.mark.parametrize(` to configure the declaration immediately below.
@pytest.mark.parametrize(
    # Supplies this item to the surrounding call or collection.
    ("value", "code"),
    # Begins the nested block or multiline expression completed below.
    [
        # Supplies this item to the surrounding call or collection.
        ("", "EMPTY_GUESS"),
        # Supplies this item to the surrounding call or collection.
        ("quit", "QUIT_REQUESTED"),
        # Supplies this item to the surrounding call or collection.
        ("R,,B,G,Y", "MALFORMED_GUESS"),
        # Supplies this item to the surrounding call or collection.
        ([], "EMPTY_GUESS"),
        # Supplies this item to the surrounding call or collection.
        (["R", ""], "EMPTY_GUESS"),
        # Closes the multiline call, declaration, or collection started above.
    ],
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_normalization_error_paths` callable and its typed interface.
def test_normalization_error_paths(value: str | list[str], code: str) -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError) as error:
        # Calls `normalize_code` with the supplied values.
        normalize_code(value)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == code


# Defines the `test_unknown_guess_colour_path` callable and its typed interface.
def test_unknown_guess_colour_path() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError) as error:
        # Calls `validate_code` with the supplied values.
        validate_code(["R", "B", "G", "Z"], get_preset("normal"))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == "UNKNOWN_COLOUR"


# Defines the `test_daily_short_key_and_rejection_sampling_loop` callable and its typed interface.
def test_daily_short_key_and_rejection_sampling_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    # Computes and stores `config` for subsequent operations.
    config = GameConfig(tuple("RBGYWKOPCM"), 6, 8, False)
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.raises(DomainError) as error:
        # Calls `derive_daily_secret` with the supplied values.
        derive_daily_secret(date(2026, 7, 15), config, b"short")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert error.value.code == "INVALID_DAILY_KEY"

    # Defines the `Digest` class and its related behavior.
    class Digest:
        # Defines the `__init__` callable and its typed interface.
        def __init__(self, value: bytes) -> None:
            # Computes and stores `self.value` for subsequent operations.
            self.value = value

        # Defines the `digest` callable and its typed interface.
        def digest(self) -> bytes:
            # Returns this result to the caller and ends the current function.
            return self.value

    # Defines the `fake_new` callable and its typed interface.
    def fake_new(_key: bytes, message: bytes, _algorithm: object) -> Digest:
        # Computes and stores `counter` for subsequent operations.
        counter = int.from_bytes(message[-4:], "big")
        # Checks this condition before executing the nested branch.
        if counter == 0:
            # Returns this result to the caller and ends the current function.
            return Digest(bytes([255] * 20 + [0] * 12))
        # Returns this result to the caller and ends the current function.
        return Digest(bytes(range(32)))

    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(hmac, "new", fake_new)
    # Computes and stores `secret` for subsequent operations.
    secret = derive_daily_secret(date(2026, 7, 15), config, b"x" * 32)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert secret == ("R", "B", "G", "Y", "W", "K")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(set(secret)) == config.code_length


# Defines the `test_terminal_status_property_both_paths` callable and its typed interface.
def test_terminal_status_property_both_paths() -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert GameStatus.WON.terminal is True
    # Asserts this invariant so an unexpected test state fails immediately.
    assert GameStatus.ACTIVE.terminal is False
