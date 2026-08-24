# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports selected names from `.models` for use in this module.
from .models import GameConfig, GameStatus, ScoreBreakdown


# Defines the `calculate_score` function and begins its typed parameter list.
def calculate_score(
    # Declares `config` as `GameConfig,` so the data shape is explicit.
    config: GameConfig,
    # Makes all following function parameters keyword-only for clearer call sites.
    *,
    # Declares `status` as `GameStatus,` so the data shape is explicit.
    status: GameStatus,
    # Declares `attempts_used` as `int,` so the data shape is explicit.
    attempts_used: int,
    # Declares `elapsed_seconds` as `float,` so the data shape is explicit.
    elapsed_seconds: float,
# Completes the function signature and declares the type returned to callers.
) -> ScoreBreakdown:
    # Documents the purpose and contract of the surrounding module or function.
    """Calculate the points awarded for a terminal game.

    ``elapsed_seconds`` remains part of the public call signature because callers
    persist it for leaderboard tie-breaking. Time never contributes points.
    """

    # Tests `status is not GameStatus.WON` before running the nested branch.
    if status is not GameStatus.WON:
        # Returns `ScoreBreakdown(attempts=0, difficulty=0, time=0, total=0)` to the caller as
        # this function's result.
        return ScoreBreakdown(attempts=0, difficulty=0, time=0, total=0)
    # Computes `max(0, config.max_attempts - attempts_used + 1) * 100` and stores the result in
    # `attempts_component` for later use.
    attempts_component = max(0, config.max_attempts - attempts_used + 1) * 100
    # Computes `(` and stores the result in `difficulty_component` for later use.
    difficulty_component = (
        # Continues the surrounding expression or executes the next required operation.
        config.code_length * 50
        # Continues the surrounding expression or executes the next required operation.
        + len(config.colours) * 20
        # Continues the surrounding expression or executes the next required operation.
        + (100 if config.duplicates_allowed else 0)
    # Closes the multiline call or collection started on an earlier line.
    )
    # Begins constructing the value that this function returns to its caller.
    return ScoreBreakdown(
        # Provides `attempts_component` as the `attempts` parameter or argument.
        attempts=attempts_component,
        # Provides `difficulty_component` as the `difficulty` parameter or argument.
        difficulty=difficulty_component,
        # Provides `0` as the `time` parameter or argument.
        time=0,
        # Provides `max(0, attempts_component + difficulty_component)` as the `total` parameter
        # or argument.
        total=max(0, attempts_component + difficulty_component),
    # Closes the multiline call or collection started on an earlier line.
    )
