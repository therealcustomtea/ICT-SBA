from __future__ import annotations

import json
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mastermind_core import DomainError

from .config import Settings


@dataclass(frozen=True, slots=True)
class EncryptedSecret:
    ciphertext: bytes
    nonce: bytes
    key_version: str


class SecretCipher:
    def __init__(self, keys: dict[str, bytes], active_version: str) -> None:
        if active_version not in keys:
            raise RuntimeError("The active secret encryption key version is not configured.")
        for key in keys.values():
            if len(key) not in {16, 24, 32}:
                raise RuntimeError("AES-GCM encryption keys must be 128, 192, or 256 bits.")
        self._keys = keys
        self._active_version = active_version

    @classmethod
    def from_settings(cls, settings: Settings) -> SecretCipher:
        if not settings.secret_encryption_keys:
            raise RuntimeError("MASTERMIND_SECRET_ENCRYPTION_KEYS is required.")
        try:
            keys = settings.secret_encryption_keyring()
        except ValueError as exc:
            raise RuntimeError("Secret encryption keyring is malformed.") from exc
        return cls(keys, settings.secret_active_key_version)

    def encrypt(self, secret: tuple[str, ...], *, context: str) -> EncryptedSecret:
        nonce = os.urandom(12)
        key = self._keys[self._active_version]
        plaintext = json.dumps(secret, separators=(",", ":")).encode()
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, context.encode())
        return EncryptedSecret(ciphertext, nonce, self._active_version)

    def decrypt(
        self,
        ciphertext: bytes,
        nonce: bytes,
        key_version: str,
        *,
        context: str,
    ) -> tuple[str, ...]:
        key = self._keys.get(key_version)
        if key is None:
            raise DomainError(
                "SECRET_KEY_UNAVAILABLE", "The game secret cannot be recovered safely."
            )
        try:
            value = json.loads(AESGCM(key).decrypt(nonce, ciphertext, context.encode()))
        except (InvalidTag, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise DomainError(
                "SECRET_DECRYPTION_FAILED", "The game secret cannot be recovered safely."
            ) from exc
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise DomainError(
                "SECRET_DECRYPTION_FAILED", "The game secret cannot be recovered safely."
            )
        return tuple(value)
