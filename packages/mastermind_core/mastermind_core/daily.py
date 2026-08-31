# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports `hashlib` so its functionality is available below.
import hashlib

# Imports `hmac` so its functionality is available below.
import hmac

# Imports selected names from `datetime` for use in this module.
from datetime import date

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError

# Imports selected names from `.models` for use in this module.
from .models import RULE_SET_VERSION, GameConfig

# Assigns `"daily_hmac_v1"` to the named `DAILY_DERIVATION_VERSION` constant used by the
# application.
DAILY_DERIVATION_VERSION = "daily_hmac_v1"


# Defines the `daily_challenge_id` function and begins its typed parameter list.
def daily_challenge_id(challenge_date: date) -> str:
    # Returns `f"{challenge_date.isoformat()}:{RULE_SET_VERSION}:{DAILY_DERIVATION_VERSION}"` to
    # the caller as this function's result.
    return f"{challenge_date.isoformat()}:{RULE_SET_VERSION}:{DAILY_DERIVATION_VERSION}"


# Defines the `derive_daily_secret` function and begins its typed parameter list.
def derive_daily_secret(
    # Declares `challenge_date` as `date,` so the data shape is explicit.
    challenge_date: date,
    # Declares `config` as `GameConfig,` so the data shape is explicit.
    config: GameConfig,
    # Declares `server_key` as `bytes,` so the data shape is explicit.
    server_key: bytes,
    # Completes the function signature and declares the type returned to callers.
) -> tuple[str, ...]:
    # Tests `len(server_key) < 32` before running the nested branch.
    if len(server_key) < 32:
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError("INVALID_DAILY_KEY", "The daily challenge key must be at least 32 bytes.")
    # Computes `(` and stores the result in `context` for later use.
    context = (
        # Adds this formatted text segment to the message being constructed.
        f"{DAILY_DERIVATION_VERSION}|{RULE_SET_VERSION}|{challenge_date.isoformat()}"
        # Continues the surrounding expression or executes the next required operation.
    ).encode()
    # Computes `[]` and stores the result in `output` for later use.
    output: list[str] = []
    # Computes `0` and stores the result in `counter` for later use.
    counter = 0
    # Repeats the nested block while `len(output) < config.code_length` remains true.
    while len(output) < config.code_length:
        # Computes `hmac.new(server_key, context + counter.to_bytes(4, "big"),
        # hashlib.sha256).digest()` and stores the result in `block` for later use.
        block = hmac.new(server_key, context + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        # Continues the surrounding expression or executes the next required operation.
        counter += 1
        # Computes `len(config.colours)` and stores the result in `palette_size` for later use.
        palette_size = len(config.colours)
        # Computes `(256 // palette_size) * palette_size` and stores the result in
        # `rejection_limit` for later use.
        rejection_limit = (256 // palette_size) * palette_size
        # Iterates through `value in block` for the nested operation.
        for value in block:
            # Tests `value >= rejection_limit` before running the nested branch.
            if value >= rejection_limit:
                # Skips the rest of this iteration and starts the next loop iteration.
                continue
            # Computes `config.colours[value % len(config.colours)]` and stores the result in
            # `colour` for later use.
            colour = config.colours[value % len(config.colours)]
            # Tests `config.duplicates_allowed or colour not in output` before running the
            # nested branch.
            if config.duplicates_allowed or colour not in output:
                # Adds the accepted colour to the daily secret being constructed.
                output.append(colour)
                # Tests `len(output) == config.code_length` before running the nested branch.
                if len(output) == config.code_length:
                    # Stops the nearest loop because its terminating condition has been reached.
                    break
    # Returns `tuple(output)` to the caller as this function's result.
    return tuple(output)
