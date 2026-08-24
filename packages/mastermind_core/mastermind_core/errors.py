# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations


# Defines `DomainError` as a specialization of `ValueError`.
class DomainError(ValueError):
    # Adds the `A safe, stable error that can cross application boundaries.` string to the
    # surrounding call or ordered collection.
    """A safe, stable error that can cross application boundaries."""

    # Defines the `__init__` function and begins its typed parameter list.
    def __init__(self, code: str, message: str) -> None:
        # Initializes the parent exception with the safe message or error details.
        super().__init__(message)
        # Stores `code` on this instance as `self.code` for later method calls.
        self.code = code
        # Stores `message` on this instance as `self.message` for later method calls.
        self.message = message


# Defines `IllegalTransitionError` as a specialization of `DomainError`.
class IllegalTransitionError(DomainError):
    # Defines the `__init__` function and begins its typed parameter list.
    def __init__(self, current: str, target: str) -> None:
        # Initializes the parent exception with the safe message or error details.
        super().__init__(
            # Adds the `ILLEGAL_GAME_TRANSITION` string to the surrounding call or ordered
            # collection.
            "ILLEGAL_GAME_TRANSITION",
            # Adds this formatted text segment to the message being constructed.
            f"A game cannot transition from {current} to {target}.",
        # Closes the multiline call or collection started on an earlier line.
        )
