# Data inventory

## Principles

Cipherboard collects only information needed to authenticate a player, operate games, protect ranked integrity, provide requested social features, moderate abuse, and run the service. It does not sell personal data, run advertising trackers, store date of birth, require a real name, or send secret codes and complete guess histories to third-party analytics.

The product is intended for users aged 13 and above. The legal entity, jurisdiction, support address, and policy effective date are deployment configuration and must pass the launch configuration check before a public release.

## Inventory

| Data | Source | Purpose | System | Sensitivity | Public? | Retention |
|---|---|---|---|---|---|---|
| Auth subject UUID, anonymous flag, session identifiers | first-party authentication | Identity, guest upgrade, session security | first-party authentication; subject UUID in app DB | Pseudonymous account data | No | Account life; deletion workflow below |
| Email/OAuth identity | User/Auth provider | Login and account recovery | first-party authentication only | Direct identifier | No | Until Auth account deletion/provider policy |
| Display name and normalized form | User | Profile, leaderboard attribution, moderation | MongoDB | User content/pseudonymous | Only when opted in and approved | Account life or moderation need |
| Locale, appearance/accessibility settings | User/device | Product preferences | MongoDB and device | Low | No | Account life; device storage until cleared |
| Game configuration, status, timing, score, eligibility | Server | Gameplay, history, statistics, ranking integrity | MongoDB | Pseudonymous activity | Selected rank fields when opted in | See retention policy |
| Normalized guesses and feedback | User/server | Authoritative game history, reconnect, disputes, statistics | MongoDB | Private gameplay | No; share output is aggregate symbols only | See retention policy |
| Active secret ciphertext, nonce, key version | Server/player code maker | Operate game fairly | MongoDB | Highly sensitive game state | Never while active | Deleted with session retention; keys separate |
| Daily date/config/derivation versions | Server | Same official daily puzzle | MongoDB | Low; HMAC key is secret-manager-only | Configuration may be public | Indefinite definitions; no HMAC material in DB |
| Friend challenge title, creator visibility, token digest, revoke/expiry | User/server | Private asynchronous challenge | MongoDB | Private user content/capability metadata | Title/rules only to token holder | See retention policy |
| Room membership, presence timestamps, safe event sequence | User/server | Real-time duel and reconnect | MongoDB/Redis | Pseudonymous activity | Only to room members | See retention policy |
| Leaderboard row and review status | Server | Public competition and anti-cheat | MongoDB/cache | Public only by consent | Score/name/rank subset | See retention policy |
| Achievement awards and statistics | Server | Profile features | MongoDB | Pseudonymous activity | Profile owner; public only if implemented and opted in | Account life or anonymized aggregate |
| Moderation state/action reason | Operator/server | Safety and abuse handling | MongoDB | Restricted | No | See retention policy |
| Administrative audit event | Operator/server | Accountability, incident investigation | MongoDB/secure log store | Restricted security record | No | See retention policy |
| Request ID, route, status, duration, release | Server | Reliability and incident response | Log/metrics platform | Operational | No | Short operational window |
| HMAC-pseudonymized actor/IP signal | Server/ingress | Abuse and rate-limit investigation | Redis/log security store | Pseudonymous security data | No | Ephemeral rate window / short security window |
| Product event category | Server | First-party product quality | Approved analytics store | Aggregated/pseudonymous | No | See retention policy |
| Support correspondence | User | Respond to requested help/security reports | Configured support system | May contain direct identifiers | No | Support-provider policy and retention below |

## Explicit exclusions

The following are not valid product analytics, logs, URLs, metrics labels, or third-party error-report fields:

- secret code or daily HMAC input/material;
- full guess sequence or private opponent feedback;
- access/refresh token, session cookie, authorization header, service/secret key;
- email address or OAuth token;
- friend/room plaintext invite token;
- challenge private content beyond a categorized validation error;
- raw IP address in product analytics;
- encryption key, plaintext, nonce+ciphertext bundle, or environment dump.

## Processors and access

The production privacy notice names the actually selected hosting, authentication, email, error-reporting, support, and analytics processors. A processor is not enabled until its purpose, data fields, region, retention, deletion support, DPA, security review, and owner are recorded in the launch checklist.

Access follows least privilege. Support does not receive database or secret-manager access. Engineers use approved operational views and pseudonymous identifiers. Raw production database access is break-glass, time-bounded, MFA-protected, and audited.

## User controls

Players can use an anonymous authenticated identity, opt out of public leaderboards, change or remove their display name, revoke challenges, export their profile/game data, and request account deletion. Export uses authenticated server data and applies CSV-injection protection to user-controlled fields. Account deletion is idempotent and hides public identity before external Auth cleanup.
