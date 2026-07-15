from __future__ import annotations

import itertools

import pytest
from hypothesis import given
from hypothesis import strategies as st
from mastermind_core import DomainError, calculate_feedback


@pytest.mark.parametrize(
    ("secret", "guess", "expected"),
    [
        ("RBGY", "RBGY", (4, 0)),
        ("RBGY", "WKOP", (0, 0)),
        ("RBGY", "RGBW", (1, 2)),
        ("RBGY", "RRRR", (1, 0)),
        ("RRBG", "RRRY", (2, 0)),
        ("RBRG", "RRBY", (1, 2)),
    ],
)
def test_mandatory_feedback_examples(secret: str, guess: str, expected: tuple[int, int]) -> None:
    feedback = calculate_feedback(secret, guess)
    assert (feedback.black, feedback.white) == expected


def test_exhaustive_duplicate_combinations() -> None:
    colours = "RBG"
    for secret in itertools.product(colours, repeat=4):
        for guess in itertools.product(colours, repeat=4):
            feedback = calculate_feedback(secret, guess)
            assert 0 <= feedback.black <= 4
            assert 0 <= feedback.white <= 4
            assert feedback.black + feedback.white <= 4
            assert feedback == calculate_feedback(secret, guess)


@given(
    st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10),
    st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10),
)
def test_feedback_invariants(secret: list[str], guess: list[str]) -> None:
    if len(secret) != len(guess):
        with pytest.raises(DomainError, match="lengths must match"):
            calculate_feedback(secret, guess)
        return
    feedback = calculate_feedback(secret, guess)
    assert 0 <= feedback.black <= len(secret)
    assert 0 <= feedback.white <= len(secret)
    assert feedback.black + feedback.white <= len(secret)


@given(st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10))
def test_exact_equality_is_all_black(code: list[str]) -> None:
    assert calculate_feedback(code, code).black == len(code)
    assert calculate_feedback(code, code).white == 0
