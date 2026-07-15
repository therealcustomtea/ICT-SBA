# Product requirements

## Product

Cipherboard is a consumer Mastermind game for people aged 13 and above. A first-time visitor can receive an anonymous authenticated identity and begin an Easy, Normal, Hard, Expert, practice, custom, pass-and-play, daily, friend, or private duel experience without creating a permanent account.

The service avoids advertising trackers, gambling mechanics, manipulative streak pressure, and collection of date of birth. A linked account adds cross-device history, a moderated display name, durable achievements, public leaderboard opt-in, export, and deletion controls without discarding guest history.

## Rules

- Available colours: 5–10 stable identifiers.
- Code length: 3–6.
- Attempts: 1–20.
- Duplicates: explicit per configuration; palette size must cover code length when disabled.
- Feedback: exact-position matches first, followed by unmatched colour counts. No peg is counted twice.
- Invalid guesses do not change attempts, score, timer history, or persistence.
- Valid lifecycle: created → active → won, lost, abandoned, or expired.
- Active secrets are generated and retained only by the server and are never written to browser storage.

## Official presets

| Preset | Colours | Length | Attempts | Duplicates | Ranked |
| --- | ---: | ---: | ---: | --- | --- |
| Easy | 5 | 4 | 12 | No | Yes |
| Normal | 6 | 4 | 10 | Yes | Yes |
| Hard | 8 | 5 | 8 | Yes | Yes |
| Expert | 10 | 6 | 8 | Yes | Yes |

Custom and practice games are unranked by default.

## Primary experiences

### Solo and practice

Setup exposes meaningful settings without overwhelming a new player. The board shows current and submitted rows, exact and misplaced feedback using symbols and labels, attempts remaining, safe elapsed time, rules access, connection state, and abandonment. Results show permitted secret disclosure, score breakdown, achievements, rank when eligible, safe share text, replay, and navigation home.

### Daily

One puzzle exists per UTC date and derivation version. The first valid guess begins the official run. Refresh and reconnect restore it. An identity has one official outcome; later attempts are visibly unranked practice. A session crossing midnight remains attached to its original date.

### Friend challenge

A creator chooses valid rules, optional bounded title, display-name privacy, generated or human secret, and expiry. The server returns one high-entropy share link, stores no sequential public identifier, encrypts the secret, and limits enumeration. Each solver receives one official outcome and may replay unranked. Only the creator can revoke or see aggregate completed results.

### Private duel

Two authorized members receive the same server-generated code and submit private guesses independently. Opponents see only presence, attempt count, and terminal progress. Server receipt time and a documented tie window decide the result. Durable sequence numbers restore a reconnecting client without duplicate effects.

## Profiles and competition

Statistics derive from authoritative games: games played/won, win rate, average winning attempts, best score by official difficulty, daily history/streak, fastest eligible solve, total feedback pegs, favourite mode, recent games, and earned achievements. Public leaderboards are bounded, indexed, paginated, opt-in, moderation-aware, and use deterministic ties.

Launch achievements are First Break, One Shot, No Waste, Daily Debut, Logic Week, Hard Mode, Expert Breaker, Challenger, and Duelist. Awards are server-side and idempotent.

## Administration

Authorized staff can view safe product metrics and operational state, invalidate entries, moderate names, revoke challenges, terminate rooms, change feature flags, restrict accounts, reverse supported actions, and read audit events. Every mutation requires a reason and writes actor, action, target, and timestamp. Secret plaintext and unnecessary PII are never shown.

## Quality targets

Targets are not measurements:

- Lighthouse performance ≥90 and accessibility 100 where achievable.
- LCP p75 <2.5 s, CLS <0.1, INP <200 ms.
- attempt feedback p95 <250 ms;
- normal read and cached leaderboard p95 <300 ms;
- WebSocket propagation p95 <500 ms.

Measured results belong in deployment evidence, never in this requirement document.
