from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from .config import Settings, get_settings
from .crypto import SecretCipher


@lru_cache
def _cipher_for_keyring(keyring: str, active_version: str) -> SecretCipher:
    settings = Settings(
        environment="test",
        secret_encryption_keys=keyring,
        secret_active_key_version=active_version,
    )
    return SecretCipher.from_settings(settings)


def get_cipher(settings: Settings = Depends(get_settings)) -> SecretCipher:
    return _cipher_for_keyring(settings.secret_encryption_keys, settings.secret_active_key_version)
