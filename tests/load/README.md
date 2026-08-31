# Load profiles

These k6 profiles exercise real authenticated API paths; they do not use mock responses or create sample production users. Run them against an isolated load environment with production-like MongoDB/Redis topology and a test first-party authentication project. Set `K6_TARGET_ENVIRONMENT` for every non-loopback target; use `load` or `staging` for an approved non-production environment.

Gameplay creation, first-attempt, and leaderboard reads:

```bash
K6_API_ORIGIN=https://api.load.example \
K6_TARGET_ENVIRONMENT=load \
K6_ACCESS_TOKENS_JSON='["short-lived-test-token-1","short-lived-test-token-2"]' \
K6_GAME_RATE=25 \
K6_GAME_TIME_UNIT=1s \
K6_PROFILE_DURATION=5m \
k6 run tests/load/gameplay.js
```

`K6_ACCESS_TOKEN` remains available for a one-identity smoke run. Higher request rates require enough restricted test identities and approved load-generator source IPs to stay within the deployed per-subject and per-IP rate limits. Do not raise or bypass the production security limits merely to make a profile pass.

WebSocket ticket/connect/heartbeat churn requires each token subject to already belong to its paired room. A one-member smoke run uses `K6_ACCESS_TOKEN` and `K6_ROOM_ID` and defaults to one VU, keeping both concurrent sockets and repeated ticket issuance within the default security budgets:

```bash
K6_API_ORIGIN=https://api.load.example \
K6_TARGET_ENVIRONMENT=load \
K6_ACCESS_TOKEN='short-lived-test-token' \
K6_ROOM_ID='room-uuid' \
K6_WS_VUS=1 \
K6_PROFILE_DURATION=5m \
k6 run tests/load/realtime.js
```

For a higher-concurrency WebSocket run, provide `K6_WS_TARGETS_JSON` as a JSON array of `{ "accessToken": "…", "roomId": "…" }` member pairs. The profile assigns each VU to one pair and refuses a VU count above `distinct identities × K6_WS_CONNECTIONS_PER_IDENTITY` or `K6_WS_CONNECTIONS_PER_SOURCE_IP`; both budgets default to the application defaults of 3 and 20. The 60-second action budget also covers ticket issuance with a weight of 8, so short churn sessions generally need one distinct member/room pair per VU even when the socket ceiling permits more. Shard generators so each subject, room, and source IP remains below its deployed ceiling.

The real-time connection obtains a 60-second, single-use ticket over authenticated HTTP, keeps credentials out of the URL, offers `cipherboard-v1` and `ticket.{ticket}` in `Sec-WebSocket-Protocol`, verifies that the server negotiates only `cipherboard-v1`, and sends versioned heartbeat frames. It also checks the versioned event envelope, heartbeat acknowledgement, and absence of credential or secret fields.

Use `K6_PROFILE_DURATION` for scenario length. Do not set k6's built-in `K6_DURATION`: it replaces the script's scenario and discards the configured arrival-rate/VU model.

The profiles refuse a non-loopback origin without an explicit environment label and refuse `K6_TARGET_ENVIRONMENT=production` unless `K6_ALLOW_PRODUCTION=true` is deliberately set. Production load testing additionally requires an approved change window, traffic ceiling, on-call coverage, database/Redis capacity alarms, and rollback/abort owner. Never put tokens in committed scripts, shell history, process arguments, or CI artifacts; inject short-lived restricted identities through the approved secret mechanism immediately before the run and revoke them afterward.

Record request rate, p50/p95/p99, errors, API/DB pool saturation, lock waits, Redis latency/eviction, WebSocket propagation/reconnect, instance CPU/memory, release, dataset scale, and exact profile settings. Targets are acceptance thresholds, not claims; only measured results may be reported as performance evidence.
