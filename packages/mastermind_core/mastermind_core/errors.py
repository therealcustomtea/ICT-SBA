from __future__ import annotations


class DomainError(ValueError):
    """A safe, stable error that can cross application boundaries."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class IllegalTransitionError(DomainError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            "ILLEGAL_GAME_TRANSITION",
            f"A game cannot transition from {current} to {target}.",
        )
