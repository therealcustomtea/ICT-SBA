from __future__ import annotations

import re
from collections.abc import Sequence

from .errors import DomainError
from .models import GameConfig

SEPARATOR_RE = re.compile(r"[\s,\-]+")


def normalize_code(value: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise DomainError("EMPTY_GUESS", "Enter a complete guess.")
        if stripped.lower() == "quit":
            raise DomainError("QUIT_REQUESTED", "The player asked to quit.")
        if stripped[0] in ",-" or stripped[-1] in ",-" or re.search(r"[,\-]{2,}", stripped):
            raise DomainError(
                "MALFORMED_GUESS", "Separate colour codes with spaces, commas, or hyphens."
            )
        tokens = (
            list(stripped)
            if stripped.isalpha() and len(stripped) > 1
            else SEPARATOR_RE.split(stripped)
        )
    else:
        tokens = [str(token).strip() for token in value]
        if not tokens or any(not token for token in tokens):
            raise DomainError("EMPTY_GUESS", "Enter a complete guess.")
    return tuple(token.upper() for token in tokens)


def validate_code(value: str | Sequence[str], config: GameConfig) -> tuple[str, ...]:
    code = normalize_code(value)
    if len(code) != config.code_length:
        raise DomainError(
            "INVALID_GUESS_LENGTH",
            f"Your guess must contain exactly {config.code_length} pegs.",
        )
    unknown = sorted(set(code).difference(config.colours))
    if unknown:
        raise DomainError(
            "UNKNOWN_COLOUR",
            f"Unknown or disabled colour: {', '.join(unknown)}.",
        )
    if not config.duplicates_allowed and len(set(code)) != len(code):
        raise DomainError("DUPLICATES_NOT_ALLOWED", "This game does not allow duplicate colours.")
    return code
