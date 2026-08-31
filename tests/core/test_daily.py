# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `datetime` for use in this module.
from datetime import date

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import daily_challenge_id, derive_daily_secret, get_preset


# Defines the `test_daily_is_deterministic_and_date_bound` callable and its typed interface.
def test_daily_is_deterministic_and_date_bound() -> None:
    # Computes and stores `key` for subsequent operations.
    key = b"a" * 32
    # Computes and stores `config` for subsequent operations.
    config = get_preset("normal")
    # Computes and stores `first` for subsequent operations.
    first = derive_daily_secret(date(2026, 7, 15), config, key)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first == derive_daily_secret(date(2026, 7, 15), config, key)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first != derive_daily_secret(date(2026, 7, 16), config, key)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert daily_challenge_id(date(2026, 7, 15)) == ("2026-07-15:rules_v1:daily_hmac_v1")


# Defines the `test_daily_rejection_sampling_is_deterministic_for_ten_colours` callable and its
# typed interface.
def test_daily_rejection_sampling_is_deterministic_for_ten_colours() -> None:
    # Computes and stores `config` for subsequent operations.
    config = get_preset("expert")
    # Computes and stores `values` for subsequent operations.
    values = [derive_daily_secret(date(2026, 1, day), config, b"z" * 32) for day in range(1, 20)]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert values == [
        # Calls `derive_daily_secret` with the supplied values.
        derive_daily_secret(date(2026, 1, day), config, b"z" * 32)
        # Continues the surrounding expression or operation.
        for day in range(1, 20)
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all(set(secret).issubset(set(config.colours)) for secret in values)
