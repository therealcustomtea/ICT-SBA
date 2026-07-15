from __future__ import annotations

import hashlib
import hmac
from datetime import date

from .errors import DomainError
from .models import RULE_SET_VERSION, GameConfig

DAILY_DERIVATION_VERSION = "daily_hmac_v1"


def daily_challenge_id(challenge_date: date) -> str:
    return f"{challenge_date.isoformat()}:{RULE_SET_VERSION}:{DAILY_DERIVATION_VERSION}"


def derive_daily_secret(
    challenge_date: date,
    config: GameConfig,
    server_key: bytes,
) -> tuple[str, ...]:
    if len(server_key) < 32:
        raise DomainError("INVALID_DAILY_KEY", "The daily challenge key must be at least 32 bytes.")
    context = (
        f"{DAILY_DERIVATION_VERSION}|{RULE_SET_VERSION}|{challenge_date.isoformat()}"
    ).encode()
    output: list[str] = []
    counter = 0
    while len(output) < config.code_length:
        block = hmac.new(server_key, context + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        counter += 1
        palette_size = len(config.colours)
        rejection_limit = (256 // palette_size) * palette_size
        for value in block:
            if value >= rejection_limit:
                continue
            colour = config.colours[value % len(config.colours)]
            if config.duplicates_allowed or colour not in output:
                output.append(colour)
                if len(output) == config.code_length:
                    break
    return tuple(output)
