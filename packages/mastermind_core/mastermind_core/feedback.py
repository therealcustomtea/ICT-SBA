# ruff: noqa: I001 -- line explanations intentionally separate imports.
# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports selected names from `collections` for use in this module.
from collections import Counter
# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Sequence

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError
# Imports selected names from `.models` for use in this module.
from .models import Feedback


# Defines the `calculate_feedback` function and begins its typed parameter list.
def calculate_feedback(secret: Sequence[str], guess: Sequence[str]) -> Feedback:
    # Tests `len(secret) != len(guess)` before running the nested branch.
    if len(secret) != len(guess):
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError("SEQUENCE_LENGTH_MISMATCH", "Secret and guess lengths must match.")
    # Computes `0` and stores the result in `black` for later use.
    black = 0
    # Computes `[]` and stores the result in `unmatched_secret` for later use.
    unmatched_secret: list[str] = []
    # Computes `[]` and stores the result in `unmatched_guess` for later use.
    unmatched_guess: list[str] = []
    # Iterates through `secret_peg, guess_peg in zip(secret, guess, strict=True)` for the nested
    # operation.
    for secret_peg, guess_peg in zip(secret, guess, strict=True):
        # Tests `secret_peg == guess_peg` before running the nested branch.
        if secret_peg == guess_peg:
            # Continues the surrounding expression or executes the next required operation.
            black += 1
        # Handles the remaining case when the preceding conditions were false.
        else:
            # Records this unmatched secret peg for later colour-only comparison.
            unmatched_secret.append(secret_peg)
            # Records this unmatched guessed peg for later colour-only comparison.
            unmatched_guess.append(guess_peg)
    # Computes `Counter(unmatched_secret)` and stores the result in `secret_counts` for later
    # use.
    secret_counts = Counter(unmatched_secret)
    # Computes `Counter(unmatched_guess)` and stores the result in `guess_counts` for later use.
    guess_counts = Counter(unmatched_guess)
    # Computes `sum((secret_counts & guess_counts).values())` and stores the result in `white`
    # for later use.
    white = sum((secret_counts & guess_counts).values())
    # Returns `Feedback(black=black, white=white)` to the caller as this function's result.
    return Feedback(black=black, white=white)
