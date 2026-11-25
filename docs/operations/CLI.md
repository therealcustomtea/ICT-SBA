# Cipherboard command-line client

The CLI provides offline Mastermind and the GUI's account-backed game workflows. Offline scores remain local CSV records. Online games, daily results, friend challenges, rooms, profiles, achievements, and rankings use the same FastAPI service and account data as the GUI.

## Start

```bash
uv sync --frozen --all-extras
uv run python -m mastermind_cli
```

The original options 1–5 are preserved. Option **6** opens online features. To open that menu directly:

```bash
docker compose up -d mongo redis mailpit api
uv run python -m mastermind_cli --online
```

For a hosted service, supply the API and the web origin allowed by that server's WebSocket policy:

```bash
uv run python -m mastermind_cli --online \
  --api-url https://api.example.com \
  --product-origin https://play.example.com
```

Remote API connections require HTTPS. `--allow-http` is an explicit exception for a trusted development network; the desktop container uses it to reach `http://api:8000` inside Docker. Published privacy and terms text additionally requires the web service.

## Online menu

| Menu | Actions |
| --- | --- |
| Play | Solo, practice, custom settings, and human Code Maker pass-and-play |
| History | Paginated account games, result inspection, and resuming by game ID |
| Daily | One official UTC puzzle, restoration, unranked replay, and daily rankings |
| Friends | Create and play challenges, private share codes, creator results, and revocation |
| Rooms | Create/join, ready, private guesses, live progress, reconnect, replay, and abandonment |
| Profile | Display name, public-ranking opt-in, statistics, achievements, and progress |
| Leaderboards | Weekly/all-time, difficulty filters, pagination, and personal rank |
| Account | Guest identity, email sign-in/upgrade, authenticator MFA, ZIP export, deletion, logout |
| Settings | English/Traditional Chinese, terminal palette, patterns/high contrast, sound, analytics consent |
| Support | Submit an explicitly confirmed support request |
| Admin | Authorized summaries, lists, flags, audited moderation, revocation, and room termination |
| Rules/privacy | Terminal rules and readable published privacy/terms pages |

Browser-specific presentation, PWA installation, touch gestures, and browser animation do not apply to a terminal. The CLI provides keyboard interaction, static output, labelled feedback, and optional pattern identifiers.

## Sign in and keep a session

Online mode restores the saved refresh cookie or obtains a guest identity. In **Account**, request an email link and paste the unopened link into **Verify email link**. The CLI accepts the API's own origin or the public issuer advertised by that API's session, then submits the token to the configured API without following browser redirects. Local desktop emails appear in Mailpit at `http://127.0.0.1:8025`.

MFA setup displays the private authenticator key/URI once; add it to your authenticator and verify its six-digit code. Administrative grants, recent authentication, registered-account requirements, ownership checks, feature flags, and server rate limits remain enforced by the API. The CLI cannot grant itself permissions.

Per-server state is stored under `~/.config/cipherboard/cli/<server hash>/state.json`. Access tokens stay in memory. The state contains the refresh cookie, preferences, room sequence cursors, and unacknowledged guesses; it does not contain server-generated secrets or MFA keys. POSIX files use mode 0600 and directories mode 0700. Windows relies on the user's profile permissions. Do not share this directory or upload it.

One process holds a session-directory lock to avoid racing refresh-token rotation. Use a different state directory for a second player:

```bash
uv run python -m mastermind_cli --online --state-dir "$HOME/.config/cipherboard/player-two"
```

Use **Sign out** to revoke the presented session and remove local account state. A lost network connection can prevent server revocation; local credentials are still cleared.

## Games and reconnection

`back` or `quit` returns to the online menu and preserves the game. `abandon` explicitly ends it after confirmation. `refresh` reloads authoritative state. If a guess has an uncertain outcome, `retry` reuses its saved idempotency key; a second guess cannot replace an unacknowledged submission. Invalid guesses leave the server's attempt count unchanged.

The daily service resumes an existing active official run before allowing a practice replay. Room guests see only permitted opponent progress. Heartbeats run independently of terminal input; reconnect obtains a fresh one-use ticket and supplies the last durable sequence. Keep the room ID to resume from another CLI session.

## Exports and accessibility

Offline menu option 4 exports CSV summaries. **Account export** downloads the server's protected ZIP, including permitted account history. Existing export files require explicit replacement confirmation. Account deletion requires the exact word `DELETE` and recent authentication.

`--locale zh-Hant` selects Traditional Chinese. Terminal letters remain visible with colour disabled; `NO_COLOR` and `TERM=dumb` disable ANSI output. High contrast uses plain letters with pattern numbers. Terminal motion is always reduced because output is static. Analytics are off by default and consented events use the API's closed schema without guesses or secrets.

## Verification

Offline and transport checks can run without services:

```bash
uv run pytest tests/core tests/cli/test_app.py tests/cli/test_storage.py tests/cli/test_online.py
```

The CLI's API and live room integration tests require an isolated MongoDB replica set and Redis. See [Testing](TESTING.md). They exercise real authentication, game and account handlers, two-client WebSocket submissions, replay, permission denial, and the actual module entry point. Use test service URLs and test keys; never production data.
