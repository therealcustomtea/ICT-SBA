from __future__ import annotations

from .models import GameConfig, GameStatus, ScoreBreakdown


def calculate_score(
    config: GameConfig,
    *,
    status: GameStatus,
    attempts_used: int,
    elapsed_seconds: float,
) -> ScoreBreakdown:
    """Calculate the points awarded for a terminal game.

    ``elapsed_seconds`` remains part of the public call signature because callers
    persist it for leaderboard tie-breaking. Time never contributes points.
    """

    if status is not GameStatus.WON:
        return ScoreBreakdown(attempts=0, difficulty=0, time=0, total=0)
    attempts_component = max(0, config.max_attempts - attempts_used + 1) * 100
    difficulty_component = (
        config.code_length * 50
        + len(config.colours) * 20
        + (100 if config.duplicates_allowed else 0)
    )
    return ScoreBreakdown(
        attempts=attempts_component,
        difficulty=difficulty_component,
        time=0,
        total=max(0, attempts_component + difficulty_component),
    )
