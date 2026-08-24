# ruff: noqa: I001 -- line explanations intentionally separate imports.
# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports `re` so its functionality is available below.
import re
# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Sequence

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError
# Imports selected names from `.models` for use in this module.
from .models import GameConfig

# Assigns `re.compile(r"[\s,\-]+")` to the named `SEPARATOR_RE` constant used by the
# application.
SEPARATOR_RE = re.compile(r"[\s,\-]+")


# Defines the `normalize_code` function and begins its typed parameter list.
def normalize_code(value: str | Sequence[str]) -> tuple[str, ...]:
    # Tests `isinstance(value, str)` before running the nested branch.
    if isinstance(value, str):
        # Computes `value.strip()` and stores the result in `stripped` for later use.
        stripped = value.strip()
        # Tests `not stripped` before running the nested branch.
        if not stripped:
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("EMPTY_GUESS", "Enter a complete guess.")
        # Tests `stripped.lower() == "quit"` before running the nested branch.
        if stripped.lower() == "quit":
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("QUIT_REQUESTED", "The player asked to quit.")
        # Tests `stripped[0] in ",-" or stripped[-1] in ",-" or re.search(r"[,\-]{2,}",
        # stripped)` before running the nested branch.
        if stripped[0] in ",-" or stripped[-1] in ",-" or re.search(r"[,\-]{2,}", stripped):
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError(
                # Adds the `MALFORMED_GUESS", "Separate colour codes with spaces, commas, or
                # hyphens.` string to the surrounding call or ordered collection.
                "MALFORMED_GUESS", "Separate colour codes with spaces, commas, or hyphens."
            # Closes the multiline call or collection started on an earlier line.
            )
        # Computes `(` and stores the result in `tokens` for later use.
        tokens = (
            # Calls `list` to perform this step with the supplied arguments.
            list(stripped)
            # Tests `stripped.isalpha() and len(stripped) > 1` before running the nested branch.
            if stripped.isalpha() and len(stripped) > 1
            # Continues the surrounding expression or executes the next required operation.
            else SEPARATOR_RE.split(stripped)
        # Closes the multiline call or collection started on an earlier line.
        )
    # Handles the remaining case when the preceding conditions were false.
    else:
        # Computes `[str(token).strip() for token in value]` and stores the result in `tokens`
        # for later use.
        tokens = [str(token).strip() for token in value]
        # Tests `not tokens or any(not token for token in tokens)` before running the nested
        # branch.
        if not tokens or any(not token for token in tokens):
            # Raises the specified exception to report an invalid or failed operation.
            raise DomainError("EMPTY_GUESS", "Enter a complete guess.")
    # Returns `tuple(token.upper() for token in tokens)` to the caller as this function's
    # result.
    return tuple(token.upper() for token in tokens)


# Defines the `validate_code` function and begins its typed parameter list.
def validate_code(value: str | Sequence[str], config: GameConfig) -> tuple[str, ...]:
    # Computes `normalize_code(value)` and stores the result in `code` for later use.
    code = normalize_code(value)
    # Tests `len(code) != config.code_length` before running the nested branch.
    if len(code) != config.code_length:
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError(
            # Adds the `INVALID_GUESS_LENGTH` string to the surrounding call or ordered
            # collection.
            "INVALID_GUESS_LENGTH",
            # Adds this formatted text segment to the message being constructed.
            f"Your guess must contain exactly {config.code_length} pegs.",
        # Closes the multiline call or collection started on an earlier line.
        )
    # Computes `sorted(set(code).difference(config.colours))` and stores the result in `unknown`
    # for later use.
    unknown = sorted(set(code).difference(config.colours))
    # Tests `unknown` before running the nested branch.
    if unknown:
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError(
            # Adds the `UNKNOWN_COLOUR` string to the surrounding call or ordered collection.
            "UNKNOWN_COLOUR",
            # Adds this formatted text segment to the message being constructed.
            f"Unknown or disabled colour: {', '.join(unknown)}.",
        # Closes the multiline call or collection started on an earlier line.
        )
    # Tests `not config.duplicates_allowed and len(set(code)) != len(code)` before running the
    # nested branch.
    if not config.duplicates_allowed and len(set(code)) != len(code):
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError("DUPLICATES_NOT_ALLOWED", "This game does not allow duplicate colours.")
    # Returns `code` to the caller as this function's result.
    return code
