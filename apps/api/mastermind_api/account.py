# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports the required names from `.auth` for this module.
from .auth import AuthPrincipal, revoke_user_sessions

# Imports the required names from `.database` for this module.
from .database import MongoSession

# Imports the required names from `.models` for this module.
from .models import AccountDeletionRequest, AuthEmailToken, AuthUser

# Imports the required names from `.services` for this module.
from .services import delete_account, utcnow


# Defines this callable to implement the operation described by its name.
async def process_account_deletion(
    # Declares this typed field so the surrounding contract is explicit.
    session: MongoSession,
    # Declares this typed field so the surrounding contract is explicit.
    principal: AuthPrincipal,
# Closes the multiline declaration, call, or collection opened above.
) -> None:
    # Stores `deletion` because later steps depend on this value.
    deletion = await session.find_one(
        # Supplies this required nested value.
        AccountDeletionRequest, {'user_id': principal.user_id}
    # Closes the multiline declaration, call, or collection opened above.
    )
    # Guards the nested operation so it runs only when this condition is satisfied.
    if deletion is not None and deletion.status == 'completed':
        # Returns the computed result and ends the current callable.
        return
    # Guards the nested operation so it runs only when this condition is satisfied.
    if deletion is None:
        # Stores `deletion` because later steps depend on this value.
        deletion = AccountDeletionRequest(user_id=principal.user_id)
        # Supplies this required nested value.
        session.add(deletion)
    # Stores `deletion.status` because later steps depend on this value.
    deletion.status = 'pending'
    # Stores `deletion.last_attempt_at` because later steps depend on this value.
    deletion.last_attempt_at = utcnow()
    # Performs this required operation before the surrounding flow continues.
    await delete_account(session, principal)
    # Performs this required operation before the surrounding flow continues.
    await revoke_user_sessions(session, principal.user_id)
    # Performs this required operation before the surrounding flow continues.
    await session.delete_many(AuthEmailToken, {'user_id': principal.user_id})
    # Stores `user` because later steps depend on this value.
    user = await session.get(AuthUser, principal.user_id)
    # Guards the nested operation so it runs only when this condition is satisfied.
    if user is not None:
        # Stores `user.email` because later steps depend on this value.
        user.email = None
        # Stores `user.normalized_email` because later steps depend on this value.
        user.normalized_email = None
        # Stores `user.deleted_at` because later steps depend on this value.
        user.deleted_at = utcnow()
        # Stores `user.totp_secret_ciphertext` because later steps depend on this value.
        user.totp_secret_ciphertext = None
        # Stores `user.totp_secret_nonce` because later steps depend on this value.
        user.totp_secret_nonce = None
        # Stores `user.totp_secret_key_version` because later steps depend on this value.
        user.totp_secret_key_version = None
    # Stores `deletion.status` because later steps depend on this value.
    deletion.status = 'completed'
    # Stores `deletion.last_error_code` because later steps depend on this value.
    deletion.last_error_code = None
    # Stores `deletion.completed_at` because later steps depend on this value.
    deletion.completed_at = utcnow()
    # Performs this required operation before the surrounding flow continues.
    await session.commit()
