# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `functools` for use in this module.
from functools import lru_cache

# Imports selected names from `fastapi` for use in this module.
from fastapi import Depends

# Imports selected names from `.config` for use in this module.
from .config import Settings, get_settings

# Imports selected names from `.crypto` for use in this module.
from .crypto import SecretCipher


# Applies `@lru_cache` to configure the declaration immediately below.
@lru_cache
# Defines the `_cipher_for_keyring` callable and its typed interface.
def _cipher_for_keyring(keyring: str, active_version: str) -> SecretCipher:
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=keyring,
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version=active_version,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Returns this result to the caller and ends the current function.
    return SecretCipher.from_settings(settings)


# Defines the `get_cipher` callable and its typed interface.
def get_cipher(settings: Settings = Depends(get_settings)) -> SecretCipher:
    # Returns this result to the caller and ends the current function.
    return _cipher_for_keyring(settings.secret_encryption_keys, settings.secret_active_key_version)
