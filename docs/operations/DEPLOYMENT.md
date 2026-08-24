# Deployment

Production requires managed MongoDB with TLS and backups/PITR, managed Redis over TLS, an SMTP provider, exact HTTPS origins, protected secrets, and digest-pinned API/web images.

The API runtime environment file must be mode `0600` and contain the documented `MASTERMIND_*` values, including the MongoDB URI, database name, Redis URL, auth signing key, SMTP credentials, and cryptographic keyrings. The web image receives only the documented `NEXT_PUBLIC_*` build values.

The protected deployment workflow:

1. resolves and authorizes the reviewed source SHA;
2. validates public launch configuration;
3. builds, scans, and pushes digest-pinned images;
4. copies the production Compose definition to the target;
5. runs `mastermind-initialize` with the runtime secret file;
6. starts the API and web images and checks readiness.

Required GitHub environment variables are `DEPLOY_PATH`, `RUNTIME_ENV_FILE`, and the documented browser values. Required secrets are `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_PRIVATE_KEY`, and the independently verified `DEPLOY_SSH_KNOWN_HOST`.

Only the TLS ingress is internet-facing. Ports 3000 and 8000 remain bound to loopback/private ingress. MongoDB and Redis network rules admit only workload identities. SMTP, database, Redis, signing, and encryption credentials never enter web build arguments or GitHub variables.

Run retention from an external no-overlap scheduler using the same hardened API image:

```bash
docker run --rm --env-file /run/secrets/cipherboard/runtime.env \
  ghcr.io/OWNER/REPO-api@sha256:DIGEST \
  mastermind-retention --batch-size 500 --max-batches 20
```

Alert on non-zero exits, missed executions, repeated maximum-batch exhaustion, and retention age drift. Validate guest auth, refresh rotation, email-link delivery, profile ownership, one game, leaderboard filtering, and one two-client duel before promotion.
