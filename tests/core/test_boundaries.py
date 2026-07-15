from __future__ import annotations

import hmac
from datetime import UTC, date, datetime

import pytest
from mastermind_core import (
    AttemptRecord,
    DomainError,
    Feedback,
    GameConfig,
    GameStatus,
    ScoreBreakdown,
    derive_daily_secret,
    get_preset,
    normalize_code,
    preset_name,
    validate_code,
)


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        (
            {
                "colours": tuple("RBGYR"),
                "code_length": 4,
                "max_attempts": 10,
                "duplicates_allowed": True,
            },
            "DUPLICATE_COLOUR_OPTION",
        ),
        (
            {
                "colours": ("R", "B", "G", "Y", "Z"),
                "code_length": 4,
                "max_attempts": 10,
                "duplicates_allowed": True,
            },
            "UNKNOWN_COLOUR",
        ),
        (
            {
                "colours": tuple("RBGYW"),
                "code_length": 6,
                "max_attempts": 10,
                "duplicates_allowed": False,
            },
            "INSUFFICIENT_UNIQUE_COLOURS",
        ),
        (
            {
                "colours": tuple("RBGYW"),
                "code_length": 4,
                "max_attempts": 10,
                "duplicates_allowed": True,
                "time_bonus_cap": 3601,
            },
            "INVALID_TIME_BONUS_CAP",
        ),
    ],
)
def test_configuration_rejects_each_invalid_boundary(kwargs: dict[str, object], code: str) -> None:
    with pytest.raises(DomainError) as error:
        GameConfig(**kwargs)  # type: ignore[arg-type]
    assert error.value.code == code


def test_snake_case_config_deserialization_and_value_serializers() -> None:
    config = GameConfig.from_dict(
        {
            "colours": list("RBGYW"),
            "code_length": 4,
            "max_attempts": 9,
            "duplicates_allowed": True,
            "code_maker": "computer",
            "time_bonus_cap": 60,
        }
    )
    assert config.max_attempts == 9
    feedback = Feedback(black=1, white=2)
    assert feedback.to_dict() == {"black": 1, "white": 2}
    attempt = AttemptRecord(
        number=1,
        guess=("R", "B", "G", "Y"),
        feedback=feedback,
        submitted_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    assert attempt.to_dict()["submittedAt"] == "2026-07-15T00:00:00+00:00"
    assert ScoreBreakdown(100, 200, 30, 330).to_dict()["version"] == "score_v1"


def test_negative_feedback_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        Feedback(-1, 0)
    assert error.value.code == "INVALID_FEEDBACK"


def test_preset_lookup_name_and_unknown_paths() -> None:
    assert get_preset(" EASY ") == get_preset("easy")
    assert preset_name(get_preset("hard")) == "hard"
    custom = GameConfig(tuple("RBGYW"), 3, 7, True)
    assert preset_name(custom) is None
    with pytest.raises(DomainError) as error:
        get_preset("impossible")
    assert error.value.code == "UNKNOWN_DIFFICULTY"


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("", "EMPTY_GUESS"),
        ("quit", "QUIT_REQUESTED"),
        ("R,,B,G,Y", "MALFORMED_GUESS"),
        ([], "EMPTY_GUESS"),
        (["R", ""], "EMPTY_GUESS"),
    ],
)
def test_normalization_error_paths(value: str | list[str], code: str) -> None:
    with pytest.raises(DomainError) as error:
        normalize_code(value)
    assert error.value.code == code


def test_unknown_guess_colour_path() -> None:
    with pytest.raises(DomainError) as error:
        validate_code(["R", "B", "G", "Z"], get_preset("normal"))
    assert error.value.code == "UNKNOWN_COLOUR"


def test_daily_short_key_and_rejection_sampling_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    config = GameConfig(tuple("RBGYWKOPCM"), 6, 8, False)
    with pytest.raises(DomainError) as error:
        derive_daily_secret(date(2026, 7, 15), config, b"short")
    assert error.value.code == "INVALID_DAILY_KEY"

    class Digest:
        def __init__(self, value: bytes) -> None:
            self.value = value

        def digest(self) -> bytes:
            return self.value

    def fake_new(_key: bytes, message: bytes, _algorithm: object) -> Digest:
        counter = int.from_bytes(message[-4:], "big")
        if counter == 0:
            return Digest(bytes([255] * 20 + [0] * 12))
        return Digest(bytes(range(32)))

    monkeypatch.setattr(hmac, "new", fake_new)
    secret = derive_daily_secret(date(2026, 7, 15), config, b"x" * 32)
    assert secret == ("R", "B", "G", "Y", "W", "K")
    assert len(set(secret)) == config.code_length


def test_terminal_status_property_both_paths() -> None:
    assert GameStatus.WON.terminal is True
    assert GameStatus.ACTIVE.terminal is False
