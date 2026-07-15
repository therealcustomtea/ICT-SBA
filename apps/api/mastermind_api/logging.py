from __future__ import annotations

import logging
import sys
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any

import structlog

SENSITIVE_KEY_PARTS = (
    "authorization",
    "token",
    "secret",
    "ciphertext",
    "password",
    "cookie",
    "guess",
    "email",
    "exception",
    "exc_info",
)


def _redact(value: Any, key: str = "") -> Any:
    if any(part in key.casefold() for part in SENSITIVE_KEY_PARTS):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {
            str(child_key): _redact(child_value, str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_redact(item) for item in value]
    if isinstance(value, str) and value.casefold().startswith("bearer "):
        return "[REDACTED]"
    return value


def redact_sensitive(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> Mapping[str, Any]:
    redacted = _redact(event_dict)
    return redacted if isinstance(redacted, Mapping) else {"event": "[REDACTED]"}


def configure_logging(level: str) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            redact_sensitive,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )
