from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from .errors import DomainError
from .models import Feedback


def calculate_feedback(secret: Sequence[str], guess: Sequence[str]) -> Feedback:
    if len(secret) != len(guess):
        raise DomainError("SEQUENCE_LENGTH_MISMATCH", "Secret and guess lengths must match.")
    black = 0
    unmatched_secret: list[str] = []
    unmatched_guess: list[str] = []
    for secret_peg, guess_peg in zip(secret, guess, strict=True):
        if secret_peg == guess_peg:
            black += 1
        else:
            unmatched_secret.append(secret_peg)
            unmatched_guess.append(guess_peg)
    secret_counts = Counter(unmatched_secret)
    guess_counts = Counter(unmatched_guess)
    white = sum((secret_counts & guess_counts).values())
    return Feedback(black=black, white=white)
