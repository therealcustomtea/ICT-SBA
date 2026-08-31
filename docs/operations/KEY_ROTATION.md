# Key and credential rotation

- Rotate the MongoDB Atlas database user/password through Atlas, update the secret-managed URI, roll API connections, verify readiness, then revoke the old user.
- Rotate Redis and SMTP credentials with the same add → deploy → verify → revoke sequence.
- Rotate `MASTERMIND_AUTH_SIGNING_KEY` during a controlled reauthentication window. The current HS256 implementation accepts one key, so rotation invalidates access tokens and requires refresh; revoke all refresh sessions for a suspected compromise.
- Rotate AES and daily HMAC keys by adding a new version to the keyring, changing the active version, deploying, and retaining old versions while ciphertext or historical daily definitions still reference them.
- Rotate the public-identifier HMAC key only with an explicit capability invalidation plan because existing friend/room codes will no longer resolve.

Never print keys, place them on command lines visible to process listings, add them to browser variables, or commit them. Record the credential identifier/version and verification evidence, not the secret value.
