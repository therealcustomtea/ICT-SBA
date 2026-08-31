# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `itertools` so the module can use that dependency.
import itertools

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `hypothesis` for use in this module.
from hypothesis import given

# Imports selected names from `hypothesis` for use in this module.
from hypothesis import strategies as st

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import DomainError, calculate_feedback


# Applies `@pytest.mark.parametrize(` to configure the declaration immediately below.
@pytest.mark.parametrize(
    # Supplies this item to the surrounding call or collection.
    ("secret", "guess", "expected"),
    # Begins the nested block or multiline expression completed below.
    [
        # Supplies this item to the surrounding call or collection.
        ("RBGY", "RBGY", (4, 0)),
        # Supplies this item to the surrounding call or collection.
        ("RBGY", "WKOP", (0, 0)),
        # Supplies this item to the surrounding call or collection.
        ("RBGY", "RGBW", (1, 2)),
        # Supplies this item to the surrounding call or collection.
        ("RBGY", "RRRR", (1, 0)),
        # Supplies this item to the surrounding call or collection.
        ("RRBG", "RRRY", (2, 0)),
        # Supplies this item to the surrounding call or collection.
        ("RBRG", "RRBY", (1, 2)),
        # Closes the multiline call, declaration, or collection started above.
    ],
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_mandatory_feedback_examples` callable and its typed interface.
def test_mandatory_feedback_examples(secret: str, guess: str, expected: tuple[int, int]) -> None:
    # Computes and stores `feedback` for subsequent operations.
    feedback = calculate_feedback(secret, guess)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (feedback.black, feedback.white) == expected


# Defines the `test_exhaustive_duplicate_combinations` callable and its typed interface.
def test_exhaustive_duplicate_combinations() -> None:
    # Computes and stores `colours` for subsequent operations.
    colours = "RBG"
    # Iterates through the supplied values for the nested operation.
    for secret in itertools.product(colours, repeat=4):
        # Iterates through the supplied values for the nested operation.
        for guess in itertools.product(colours, repeat=4):
            # Computes and stores `feedback` for subsequent operations.
            feedback = calculate_feedback(secret, guess)
            # Asserts this invariant so an unexpected test state fails immediately.
            assert 0 <= feedback.black <= 4
            # Asserts this invariant so an unexpected test state fails immediately.
            assert 0 <= feedback.white <= 4
            # Asserts this invariant so an unexpected test state fails immediately.
            assert feedback.black + feedback.white <= 4
            # Asserts this invariant so an unexpected test state fails immediately.
            assert feedback == calculate_feedback(secret, guess)


# Applies `@given(` to configure the declaration immediately below.
@given(
    # Calls `st.lists` with the supplied values.
    st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10),
    # Calls `st.lists` with the supplied values.
    st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10),
    # Closes the multiline call, declaration, or collection started above.
)
# Defines the `test_feedback_invariants` callable and its typed interface.
def test_feedback_invariants(secret: list[str], guess: list[str]) -> None:
    # Checks this condition before executing the nested branch.
    if len(secret) != len(guess):
        # Acquires this managed resource and guarantees cleanup afterward.
        with pytest.raises(DomainError, match="lengths must match"):
            # Calls `calculate_feedback` with the supplied values.
            calculate_feedback(secret, guess)
        # Returns this result to the caller and ends the current function.
        return
    # Computes and stores `feedback` for subsequent operations.
    feedback = calculate_feedback(secret, guess)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert 0 <= feedback.black <= len(secret)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert 0 <= feedback.white <= len(secret)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert feedback.black + feedback.white <= len(secret)


# Applies `@given(st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10))` to
# configure the declaration immediately below.
@given(st.lists(st.sampled_from(list("RBGYWKOPCM")), min_size=1, max_size=10))
# Defines the `test_exact_equality_is_all_black` callable and its typed interface.
def test_exact_equality_is_all_black(code: list[str]) -> None:
    # Asserts this invariant so an unexpected test state fails immediately.
    assert calculate_feedback(code, code).black == len(code)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert calculate_feedback(code, code).white == 0
