"""Terminal styling for Mastermind colour identifiers."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from typing import Protocol

RESET = "\x1b[0m"

# Bright foreground colours keep peg identifiers legible on light and dark terminals.
# White and black use contrasting backgrounds because a foreground alone can disappear.
ANSI_COLOURS = {
    "R": "\x1b[91m",
    "B": "\x1b[94m",
    "G": "\x1b[92m",
    "Y": "\x1b[93m",
    "W": "\x1b[30;47m",
    "K": "\x1b[97;40m",
    "O": "\x1b[38;5;208m",
    "P": "\x1b[38;5;135m",
    "C": "\x1b[96m",
    "M": "\x1b[95m",
}


class TerminalStream(Protocol):
    """Small stream contract needed for terminal capability detection."""

    def isatty(self) -> bool: ...


def supports_colour(
    stream: TerminalStream = sys.stdout,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Return whether ANSI colour should be emitted for this process."""

    environment = os.environ if environ is None else environ
    if "NO_COLOR" in environment or environment.get("TERM", "").casefold() == "dumb":
        return False
    if environment.get("FORCE_COLOR", "").casefold() not in {"", "0", "false"}:
        return True
    try:
        return stream.isatty()
    except (AttributeError, OSError):
        return False


def format_colour(identifier: str, *, enabled: bool) -> str:
    """Style one known colour identifier, or return it unchanged."""

    if not enabled or identifier not in ANSI_COLOURS:
        return identifier
    return f"{ANSI_COLOURS[identifier]}{identifier}{RESET}"


def format_code(code: Sequence[str], *, enabled: bool) -> str:
    """Format a sequence without changing its visible width."""

    return " ".join(format_colour(identifier, enabled=enabled) for identifier in code)
