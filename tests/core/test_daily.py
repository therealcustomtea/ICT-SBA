from __future__ import annotations

from datetime import date

from mastermind_core import daily_challenge_id, derive_daily_secret, get_preset


def test_daily_is_deterministic_and_date_bound() -> None:
    key = b"a" * 32
    config = get_preset("normal")
    first = derive_daily_secret(date(2026, 7, 15), config, key)
    assert first == derive_daily_secret(date(2026, 7, 15), config, key)
    assert first != derive_daily_secret(date(2026, 7, 16), config, key)
    assert daily_challenge_id(date(2026, 7, 15)) == ("2026-07-15:rules_v1:daily_hmac_v1")


def test_daily_rejection_sampling_is_deterministic_for_ten_colours() -> None:
    config = get_preset("expert")
    values = [derive_daily_secret(date(2026, 1, day), config, b"z" * 32) for day in range(1, 20)]
    assert values == [
        derive_daily_secret(date(2026, 1, day), config, b"z" * 32) for day in range(1, 20)
    ]
    assert all(set(secret).issubset(set(config.colours)) for secret in values)
