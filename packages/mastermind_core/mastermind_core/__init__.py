# Imports selected names from `.daily` for use in this module.
from .daily import DAILY_DERIVATION_VERSION, daily_challenge_id, derive_daily_secret

# Imports selected names from `.engine` for use in this module.
from .engine import abandon_game, create_game, generate_secret, seeded_rng, submit_guess

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError, IllegalTransitionError

# Imports selected names from `.feedback` for use in this module.
from .feedback import calculate_feedback

# Imports selected names from `.models` for use in this module.
from .models import (
    # Includes `COLOUR_IDS` in the surrounding import, call, or collection.
    COLOUR_IDS,
    # Includes `RULE_SET_VERSION` in the surrounding import, call, or collection.
    RULE_SET_VERSION,
    # Includes `SCORING_VERSION` in the surrounding import, call, or collection.
    SCORING_VERSION,
    # Includes `AttemptRecord` in the surrounding import, call, or collection.
    AttemptRecord,
    # Includes `CodeMakerType` in the surrounding import, call, or collection.
    CodeMakerType,
    # Includes `Feedback` in the surrounding import, call, or collection.
    Feedback,
    # Includes `GameConfig` in the surrounding import, call, or collection.
    GameConfig,
    # Includes `GameMode` in the surrounding import, call, or collection.
    GameMode,
    # Includes `GameState` in the surrounding import, call, or collection.
    GameState,
    # Includes `GameStatus` in the surrounding import, call, or collection.
    GameStatus,
    # Includes `GameVisibility` in the surrounding import, call, or collection.
    GameVisibility,
    # Includes `LeaderboardEligibility` in the surrounding import, call, or collection.
    LeaderboardEligibility,
    # Includes `ScoreBreakdown` in the surrounding import, call, or collection.
    ScoreBreakdown,
    # Closes the multiline call or collection started on an earlier line.
)

# Imports selected names from `.presets` for use in this module.
from .presets import PRESETS, get_preset, preset_name

# Imports selected names from `.scoring` for use in this module.
from .scoring import calculate_score

# Imports selected names from `.validation` for use in this module.
from .validation import normalize_code, validate_code

# Computes `[` and stores the result in `__all__` for later use.
__all__ = [
    # Adds the `COLOUR_IDS` string to the surrounding call or ordered collection.
    "COLOUR_IDS",
    # Adds the `DAILY_DERIVATION_VERSION` string to the surrounding call or ordered collection.
    "DAILY_DERIVATION_VERSION",
    # Adds the `PRESETS` string to the surrounding call or ordered collection.
    "PRESETS",
    # Adds the `RULE_SET_VERSION` string to the surrounding call or ordered collection.
    "RULE_SET_VERSION",
    # Adds the `SCORING_VERSION` string to the surrounding call or ordered collection.
    "SCORING_VERSION",
    # Adds the `AttemptRecord` string to the surrounding call or ordered collection.
    "AttemptRecord",
    # Adds the `CodeMakerType` string to the surrounding call or ordered collection.
    "CodeMakerType",
    # Adds the `DomainError` string to the surrounding call or ordered collection.
    "DomainError",
    # Adds the `Feedback` string to the surrounding call or ordered collection.
    "Feedback",
    # Adds the `GameConfig` string to the surrounding call or ordered collection.
    "GameConfig",
    # Adds the `GameMode` string to the surrounding call or ordered collection.
    "GameMode",
    # Adds the `GameState` string to the surrounding call or ordered collection.
    "GameState",
    # Adds the `GameStatus` string to the surrounding call or ordered collection.
    "GameStatus",
    # Adds the `GameVisibility` string to the surrounding call or ordered collection.
    "GameVisibility",
    # Adds the `IllegalTransitionError` string to the surrounding call or ordered collection.
    "IllegalTransitionError",
    # Adds the `LeaderboardEligibility` string to the surrounding call or ordered collection.
    "LeaderboardEligibility",
    # Adds the `ScoreBreakdown` string to the surrounding call or ordered collection.
    "ScoreBreakdown",
    # Adds the `abandon_game` string to the surrounding call or ordered collection.
    "abandon_game",
    # Adds the `calculate_feedback` string to the surrounding call or ordered collection.
    "calculate_feedback",
    # Adds the `calculate_score` string to the surrounding call or ordered collection.
    "calculate_score",
    # Adds the `create_game` string to the surrounding call or ordered collection.
    "create_game",
    # Adds the `daily_challenge_id` string to the surrounding call or ordered collection.
    "daily_challenge_id",
    # Adds the `derive_daily_secret` string to the surrounding call or ordered collection.
    "derive_daily_secret",
    # Adds the `generate_secret` string to the surrounding call or ordered collection.
    "generate_secret",
    # Adds the `get_preset` string to the surrounding call or ordered collection.
    "get_preset",
    # Adds the `normalize_code` string to the surrounding call or ordered collection.
    "normalize_code",
    # Adds the `preset_name` string to the surrounding call or ordered collection.
    "preset_name",
    # Adds the `seeded_rng` string to the surrounding call or ordered collection.
    "seeded_rng",
    # Adds the `submit_guess` string to the surrounding call or ordered collection.
    "submit_guess",
    # Adds the `validate_code` string to the surrounding call or ordered collection.
    "validate_code",
    # Closes the multiline call or collection started on an earlier line.
]
