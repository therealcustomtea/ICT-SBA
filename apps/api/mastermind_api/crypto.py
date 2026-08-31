# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `json` so the module can use that dependency.
import json

# Imports `os` so the module can use that dependency.
import os

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import dataclass

# Imports selected names from `cryptography.exceptions` for use in this module.
from cryptography.exceptions import InvalidTag

# Imports selected names from `cryptography.hazmat.primitives.ciphers.aead` for use in this module.
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import DomainError

# Imports selected names from `.config` for use in this module.
from .config import Settings


# Applies `@dataclass(frozen=True, slots=True)` to configure the declaration immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `EncryptedSecret` class and its related behavior.
class EncryptedSecret:
    # Declares the typed `ciphertext` data field.
    ciphertext: bytes
    # Declares the typed `nonce` data field.
    nonce: bytes
    # Declares the typed `key_version` data field.
    key_version: str


# Defines the `SecretCipher` class and its related behavior.
class SecretCipher:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self, keys: dict[str, bytes], active_version: str) -> None:
        # Checks this condition before executing the nested branch.
        if active_version not in keys:
            # Raises this exception to report an invalid or failed operation.
            raise RuntimeError("The active secret encryption key version is not configured.")
        # Iterates through the supplied values for the nested operation.
        for key in keys.values():
            # Checks this condition before executing the nested branch.
            if len(key) not in {16, 24, 32}:
                # Raises this exception to report an invalid or failed operation.
                raise RuntimeError("AES-GCM encryption keys must be 128, 192, or 256 bits.")
        # Computes and stores `self._keys` for subsequent operations.
        self._keys = keys
        # Computes and stores `self._active_version` for subsequent operations.
        self._active_version = active_version

    # Applies `@classmethod` to configure the declaration immediately below.
    @classmethod
    # Defines the `from_settings` callable and its typed interface.
    def from_settings(cls, settings: Settings) -> SecretCipher:
        # Checks this condition before executing the nested branch.
        if not settings.secret_encryption_keys:
            # Raises this exception to report an invalid or failed operation.
            raise RuntimeError("MASTERMIND_SECRET_ENCRYPTION_KEYS is required.")
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `keys` for subsequent operations.
            keys = settings.secret_encryption_keyring()
        # Handles the listed exception so failure remains controlled.
        except ValueError as exc:
            # Raises this exception to report an invalid or failed operation.
            raise RuntimeError("Secret encryption keyring is malformed.") from exc
        # Returns this result to the caller and ends the current function.
        return cls(keys, settings.secret_active_key_version)

    # Defines the `encrypt` callable and its typed interface.
    def encrypt(self, secret: tuple[str, ...], *, context: str) -> EncryptedSecret:
        # Computes and stores `nonce` for subsequent operations.
        nonce = os.urandom(12)
        # Computes and stores `key` for subsequent operations.
        key = self._keys[self._active_version]
        # Computes and stores `plaintext` for subsequent operations.
        plaintext = json.dumps(secret, separators=(",", ":")).encode()
        # Computes and stores `ciphertext` for subsequent operations.
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, context.encode())
        # Returns this result to the caller and ends the current function.
        return EncryptedSecret(ciphertext, nonce, self._active_version)

    # Defines the `decrypt` callable and its typed interface.
    def decrypt(
        # Declares the current instance received by this method.
        self,
        # Declares the typed `ciphertext` data field.
        ciphertext: bytes,
        # Declares the typed `nonce` data field.
        nonce: bytes,
        # Declares the typed `key_version` data field.
        key_version: str,
        # Makes the following parameters keyword-only for clear call sites.
        *,
        # Declares the typed `context` data field.
        context: str,
        # Completes the signature and declares the callable return type.
    ) -> tuple[str, ...]:
        # Computes and stores `key` for subsequent operations.
        key = self._keys.get(key_version)
        # Checks this condition before executing the nested branch.
        if key is None:
            # Raises this exception to report an invalid or failed operation.
            raise DomainError(
                # Executes this statement as the next step in the surrounding logic.
                "SECRET_KEY_UNAVAILABLE",
                # Supplies this string to the surrounding call or collection.
                "The game secret cannot be recovered safely.",
                # Closes the multiline call, declaration, or collection started above.
            )
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes and stores `value` for subsequent operations.
            value = json.loads(AESGCM(key).decrypt(nonce, ciphertext, context.encode()))
        # Handles the listed exception so failure remains controlled.
        except (InvalidTag, ValueError, TypeError, json.JSONDecodeError) as exc:
            # Raises this exception to report an invalid or failed operation.
            raise DomainError(
                # Executes this statement as the next step in the surrounding logic.
                "SECRET_DECRYPTION_FAILED",
                # Supplies this string to the surrounding call or collection.
                "The game secret cannot be recovered safely.",
                # Executes this statement as the next step in the surrounding logic.
            ) from exc
        # Checks this condition before executing the nested branch.
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            # Raises this exception to report an invalid or failed operation.
            raise DomainError(
                # Executes this statement as the next step in the surrounding logic.
                "SECRET_DECRYPTION_FAILED",
                # Supplies this string to the surrounding call or collection.
                "The game secret cannot be recovered safely.",
                # Closes the multiline call, declaration, or collection started above.
            )
        # Returns this result to the caller and ends the current function.
        return tuple(value)
