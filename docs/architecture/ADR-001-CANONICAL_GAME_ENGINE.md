# ADR-001: One canonical Python engine

- Status: accepted
- Date: 2026-07-15

## Context

The product needs identical rules in a school CLI, production API, daily derivation, tests, and future tools. Independent implementations would drift most dangerously around duplicate-colour feedback, validation, score order, and terminal transitions.

## Decision

All authoritative rules live in the pure Python `mastermind_core` package. The API and CLI import it directly. The browser may render rows and preserve an unsubmitted row, but it never decides whether an attempt is valid, calculates accepted feedback, generates a secret, finalizes a status, or assigns a score.

The core uses frozen dataclasses and explicit enums, receives an optional random source for deterministic tests, defaults to `secrets.SystemRandom`, serializes without a secret field, and persists rule/scoring version identifiers.

## Consequences

- Rule changes need one implementation and a version bump.
- Python is a required runtime for authoritative game services and CLI.
- The web needs generated contracts and server round-trips for accepted guesses.
- Pure tests can exhaust edge cases without database or network setup.

## Alternatives rejected

- Duplicate TypeScript and Python engines: rejected because equivalent-looking feedback implementations can diverge.
- Database functions for gameplay rules: rejected because they are harder to teach, test, reuse in the CLI, and version.
- Client-authoritative games: rejected because secrets, scores, daily fairness, and leaderboards would be forgeable.
