# Scoring and ranking

## `score_v1`

Only a won game receives points:

```text
attempt component = max(0, maximum attempts - attempts used + 1) × 100
difficulty component = code length × 50
                     + available colours × 20
                     + 100 when duplicates are enabled
time component = 0 (reserved in the stored breakdown for compatibility)
total = max(0, attempt component + difficulty component)
```

Losses, abandonment, and expiry score zero. The server starts and stops validated time and ignores client timestamps, but elapsed time is used only as a leaderboard tie-breaker. Components and `score_v1` are stored with the session so results remain explainable. The serialized `time` component and the legacy `timeBonusCap` configuration field remain available for record and caller compatibility; neither awards points.

Under identical settings, using fewer attempts always increases the attempt component. Official harder presets have greater difficulty components. A faster result can rank ahead only when total points and attempts are equal.

## Ranked eligibility

Eligible global entries are limited to unchanged official Easy, Normal, Hard, Expert, or official daily configurations created by the server. The attempt history must be authoritative, the profile must permit public display, and the entry must be approved. Custom, practice, pass-and-play, replay, abandoned, invalidated, banned, deleted, and hidden results remain in private history but not public rankings.

## Tie-breaking

Order is deterministic:

1. higher total score;
2. fewer attempts;
3. shorter server-validated elapsed time;
4. earlier completion timestamp;
5. immutable entry identifier for stable pagination.

## Periods

- Daily: official UTC challenge date.
- Weekly: UTC week beginning Monday.
- All-time: all eligible approved entries.
- Difficulty: filtered official preset.

The current user’s rank is computed with the same ordering even when it falls outside the requested page.

## Anti-cheat review

New entries carry a review state. Invalidated, pending-review when a surface requires approved-only data, banned, deleted, and non-public profiles are filtered at query time. Admin invalidation requires a reason and writes an audit event. Clients never submit scores or eligibility.
