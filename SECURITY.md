# Security policy

## Reporting a vulnerability

Do not open a public issue or pull request for a suspected vulnerability. Use the monitored support/security address configured for the deployed product (`NEXT_PUBLIC_SUPPORT_EMAIL`) and identify the affected deployment and release.

Include a minimal description, impact, affected route or component, safe reproduction steps, and suggested mitigation if known. Do not include active secrets, tokens, real personal data, private invite links, encryption material, or exploit traffic against another user.

Operators acknowledge reports through the configured support process, preserve evidence with restricted access, and follow `docs/operations/INCIDENT_RUNBOOK.md`. Response timing and disclosure coordination are set by the operating legal entity before launch.

## Supported versions

The current production release on the authoritative integration branch is supported. Older releases receive fixes only when needed for a controlled rollback; operators should normally move forward to a patched release.

## Security boundaries

The API is authoritative for secrets, attempts, feedback, score, achievements, rankings, and duel outcomes. first-party authentication service credentials, database owner credentials, Redis credentials, AES/HMAC keys, and error-reporting credentials are server-only. Review `docs/security/THREAT_MODEL.md` and `docs/security/SECURITY_CONTROLS.md` before changing these boundaries.
