# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `logging` so the module can use that dependency.
import logging

# Imports `sys` so the module can use that dependency.
import sys

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Mapping, MutableMapping, Sequence

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports `structlog` so the module can use that dependency.
import structlog

# Computes and stores `SENSITIVE_KEY_PARTS` for subsequent operations.
SENSITIVE_KEY_PARTS = (
    # Supplies this item to the surrounding call or collection.
    "authorization",
    # Supplies this item to the surrounding call or collection.
    "token",
    # Supplies this item to the surrounding call or collection.
    "secret",
    # Supplies this item to the surrounding call or collection.
    "ciphertext",
    # Supplies this item to the surrounding call or collection.
    "password",
    # Supplies this item to the surrounding call or collection.
    "cookie",
    # Supplies this item to the surrounding call or collection.
    "guess",
    # Supplies this item to the surrounding call or collection.
    "email",
    # Supplies this item to the surrounding call or collection.
    "exception",
    # Supplies this item to the surrounding call or collection.
    "exc_info",
    # Closes the multiline call, declaration, or collection started above.
)


# Defines the `_redact` callable and its typed interface.
def _redact(value: Any, key: str = "") -> Any:
    # Checks this condition before executing the nested branch.
    if any(part in key.casefold() for part in SENSITIVE_KEY_PARTS):
        # Returns this result to the caller and ends the current function.
        return "[REDACTED]"
    # Checks this condition before executing the nested branch.
    if isinstance(value, Mapping):
        # Returns this result to the caller and ends the current function.
        return {
            # Calls `str` with the supplied values.
            str(child_key): _redact(child_value, str(child_key))
            # Iterates through the supplied values for the nested operation.
            for child_key, child_value in value.items()
            # Closes the multiline call, declaration, or collection started above.
        }
    # Checks this condition before executing the nested branch.
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        # Returns this result to the caller and ends the current function.
        return [_redact(item) for item in value]
    # Checks this condition before executing the nested branch.
    if isinstance(value, str) and value.casefold().startswith("bearer "):
        # Returns this result to the caller and ends the current function.
        return "[REDACTED]"
    # Returns this result to the caller and ends the current function.
    return value


# Defines the `redact_sensitive` callable and its typed interface.
def redact_sensitive(
    # Declares the typed `_logger` data field.
    _logger: Any,
    # Supplies this item to the surrounding call or collection.
    _method_name: str,
    # Supplies this item to the surrounding call or collection.
    event_dict: MutableMapping[str, Any],
    # Completes the signature and declares the callable return type.
) -> Mapping[str, Any]:
    # Computes and stores `redacted` for subsequent operations.
    redacted = _redact(event_dict)
    # Returns this result to the caller and ends the current function.
    return redacted if isinstance(redacted, Mapping) else {"event": "[REDACTED]"}


# Defines the `configure_logging` callable and its typed interface.
def configure_logging(level: str) -> None:
    # Calls `logging.basicConfig` with the supplied values.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())
    # Calls `structlog.configure` with the supplied values.
    structlog.configure(
        # Computes and stores `processors` for subsequent operations.
        processors=[
            # Supplies this item to the surrounding call or collection.
            structlog.contextvars.merge_contextvars,
            # Supplies this item to the surrounding call or collection.
            structlog.processors.add_log_level,
            # Calls `structlog.processors.TimeStamper` with the supplied values.
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Calls `structlog.processors.StackInfoRenderer` with the supplied values.
            structlog.processors.StackInfoRenderer(),
            # Supplies this item to the surrounding call or collection.
            structlog.processors.format_exc_info,
            # Supplies this item to the surrounding call or collection.
            redact_sensitive,
            # Calls `structlog.processors.JSONRenderer` with the supplied values.
            structlog.processors.JSONRenderer(),
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Computes and stores `wrapper_class` for subsequent operations.
        wrapper_class=structlog.make_filtering_bound_logger(
            # Calls `getattr` with the supplied values.
            getattr(logging, level.upper(), logging.INFO)
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Provides the `cache_logger_on_first_use` parameter or keyword argument.
        cache_logger_on_first_use=True,
        # Closes the multiline call, declaration, or collection started above.
    )
