# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `base64` because this module uses that dependency.
import base64

# Imports `json` because this module uses that dependency.
import json

# Imports `jwt` because this module uses that dependency.
import jwt

# Imports `pytest` because this module uses that dependency.
import pytest

# Imports the required names from `mastermind_api.auth` for this module.
from mastermind_api.auth import AccessTokenVerifier

# Imports the required names from `mastermind_api.config` for this module.
from mastermind_api.config import Settings

# Imports the required names from `mastermind_api.crypto` for this module.
from mastermind_api.crypto import SecretCipher

# Imports the required names from `mastermind_api.errors` for this module.
from mastermind_api.errors import APIError

# Imports the required names from `mastermind_core` for this module.
from mastermind_core import DomainError

# Imports the required names from `.conftest` for this module.
from .conftest import APIContext


# Defines this callable to implement the operation described by its name.
def test_aes_gcm_round_trip_tamper_and_key_version() -> None:
    # Stores `key` because later steps depend on this value.
    key = base64.b64encode(b'k' * 32).decode()
    # Stores `cipher` because later steps depend on this value.
    cipher = SecretCipher({'v1': base64.b64decode(key)}, 'v1')
    # Stores `encrypted` because later steps depend on this value.
    encrypted = cipher.encrypt(('R', 'B', 'G', 'Y'), context='game:test')
    # Performs this required operation before the surrounding flow continues.
    assert cipher.decrypt(
        # Supplies this required nested value.
        encrypted.ciphertext,
        # Supplies this required nested value.
        encrypted.nonce,
        # Supplies this required nested value.
        encrypted.key_version,
        # Stores `context` because later steps depend on this value.
        context='game:test',
    # Closes the multiline declaration, call, or collection opened above.
    ) == ('R', 'B', 'G', 'Y')
    # Scopes this resource so acquisition and cleanup remain paired.
    with pytest.raises(DomainError):
        # Supplies this required nested value.
        cipher.decrypt(
            # Supplies this required nested value.
            encrypted.ciphertext,
            # Supplies this required nested value.
            encrypted.nonce,
            # Supplies this required nested value.
            encrypted.key_version,
            # Stores `context` because later steps depend on this value.
            context='game:other',
        # Closes the multiline declaration, call, or collection opened above.
        )


# Defines this callable to implement the operation described by its name.
def test_configuration_validates_auth_and_crypto_key_material() -> None:
    # Stores `key` because later steps depend on this value.
    key = base64.b64encode(b'e' * 32).decode()
    # Stores `settings` because later steps depend on this value.
    settings = Settings(
        # Stores `environment` because later steps depend on this value.
        environment='test',
        # Stores `auth_signing_key` because later steps depend on this value.
        auth_signing_key='a' * 32,
        # Stores `secret_encryption_keys` because later steps depend on this value.
        secret_encryption_keys=json.dumps({'v1': key}),
        # Stores `daily_hmac_key` because later steps depend on this value.
        daily_hmac_key='d' * 32,
        # Stores `public_identifier_hmac_key` because later steps depend on this value.
        public_identifier_hmac_key='i' * 32,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert settings.secret_encryption_keyring()['v1'] == b'e' * 32
    # Performs this required operation before the surrounding flow continues.
    assert settings.daily_hmac_keyring()['v1'] == b'd' * 32


# Defines this callable to implement the operation described by its name.
def test_access_token_verifier_rejects_wrong_audience_and_tampering() -> None:
    # Stores `settings` because later steps depend on this value.
    settings = Settings(
        # Stores `environment` because later steps depend on this value.
        environment='test',
        # Stores `auth_issuer` because later steps depend on this value.
        auth_issuer='https://api.example.test',
        # Stores `auth_audience` because later steps depend on this value.
        auth_audience='cipherboard-web',
        # Stores `auth_signing_key` because later steps depend on this value.
        auth_signing_key='s' * 40,
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `verifier` because later steps depend on this value.
    verifier = AccessTokenVerifier(settings)
    # Stores `wrong_audience` because later steps depend on this value.
    wrong_audience = jwt.encode(
        # Supplies this required nested value.
        {
            # Supplies this literal value to the surrounding declaration or call.
            'sub': 'bc6b03a1-3e6f-4812-b0e5-e4ec3108551f',
            # Supplies this literal value to the surrounding declaration or call.
            'sid': 'bf6d8b03-e19b-42f4-85f1-b46cb021904a',
            # Supplies this literal value to the surrounding declaration or call.
            'iss': settings.auth_issuer,
            # Supplies this literal value to the surrounding declaration or call.
            'aud': 'another-app',
            # Supplies this literal value to the surrounding declaration or call.
            'exp': 4_102_444_800,
            # Supplies this literal value to the surrounding declaration or call.
            'iat': 1_700_000_000,
            # Supplies this literal value to the surrounding declaration or call.
            'anonymous': False,
            # Supplies this literal value to the surrounding declaration or call.
            'aal': 'aal1',
        # Closes the multiline declaration, call, or collection opened above.
        },
        # Supplies this required nested value.
        settings.auth_signing_key,
        # Stores `algorithm` because later steps depend on this value.
        algorithm='HS256',
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Scopes this resource so acquisition and cleanup remain paired.
    with pytest.raises(APIError):
        # Supplies this required nested value.
        verifier.verify(wrong_audience)
    # Scopes this resource so acquisition and cleanup remain paired.
    with pytest.raises(APIError):
        # Supplies this required nested value.
        verifier.verify(f'{wrong_audience[:-1]}x')


# Defines this callable to implement the operation described by its name.
async def test_refresh_rotation_detects_reuse_and_revokes_the_family(api: APIContext) -> None:
    # Stores `guest` because later steps depend on this value.
    guest = await api.client.post('/v1/auth/guest')
    # Performs this required operation before the surrounding flow continues.
    assert guest.status_code == 201
    # Stores `old_cookie` because later steps depend on this value.
    old_cookie = api.client.cookies['cipherboard_refresh']
    # Stores `refreshed` because later steps depend on this value.
    refreshed = await api.client.post('/v1/auth/refresh')
    # Performs this required operation before the surrounding flow continues.
    assert refreshed.status_code == 200
    # Stores `new_cookie` because later steps depend on this value.
    new_cookie = api.client.cookies['cipherboard_refresh']
    # Performs this required operation before the surrounding flow continues.
    assert new_cookie != old_cookie

    # Stores `replay` because later steps depend on this value.
    replay = await api.client.post(
        # Supplies this literal value to the surrounding declaration or call.
        '/v1/auth/refresh', headers={'Cookie': f'cipherboard_refresh={old_cookie}'}
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert replay.status_code == 401
    # Stores `revoked` because later steps depend on this value.
    revoked = await api.client.post(
        # Supplies this literal value to the surrounding declaration or call.
        '/v1/auth/refresh', headers={'Cookie': f'cipherboard_refresh={new_cookie}'}
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert revoked.status_code == 401
