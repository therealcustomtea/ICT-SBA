# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports selected names from `.errors` for use in this module.
from .errors import DomainError

# Imports selected names from `.models` for use in this module.
from .models import COLOUR_IDS, GameConfig

# Assigns `{` to the named `PRESETS` constant used by the application.
PRESETS: dict[str, GameConfig] = {
    # Maps the `easy` field to `GameConfig(COLOUR_IDS[:5], 4, 12, False, ranked=True)` in the
    # dictionary.
    "easy": GameConfig(COLOUR_IDS[:5], 4, 12, False, ranked=True),
    # Maps the `normal` field to `GameConfig(COLOUR_IDS[:6], 4, 10, True, ranked=True)` in the
    # dictionary.
    "normal": GameConfig(COLOUR_IDS[:6], 4, 10, True, ranked=True),
    # Maps the `hard` field to `GameConfig(COLOUR_IDS[:8], 5, 8, True, ranked=True)` in the
    # dictionary.
    "hard": GameConfig(COLOUR_IDS[:8], 5, 8, True, ranked=True),
    # Maps the `expert` field to `GameConfig(COLOUR_IDS, 6, 8, True, ranked=True)` in the
    # dictionary.
    "expert": GameConfig(COLOUR_IDS, 6, 8, True, ranked=True),
    # Closes the multiline call or collection started on an earlier line.
}


# Defines the `get_preset` function and begins its typed parameter list.
def get_preset(name: str) -> GameConfig:
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Returns `PRESETS[name.strip().lower()]` to the caller as this function's result.
        return PRESETS[name.strip().lower()]
    # Handles the listed exception types so the program can recover safely.
    except KeyError as exc:
        # Raises the specified exception to report an invalid or failed operation.
        raise DomainError(
            # Adds the `UNKNOWN_DIFFICULTY", "Difficulty must be easy, normal, hard, or expert.`
            # string to the surrounding call or ordered collection.
            "UNKNOWN_DIFFICULTY",
            # Supplies this string to the surrounding call or collection.
            "Difficulty must be easy, normal, hard, or expert.",
            # Continues the surrounding expression or executes the next required operation.
        ) from exc


# Defines the `preset_name` function and begins its typed parameter list.
def preset_name(config: GameConfig) -> str | None:
    # Computes `config.to_dict() | {"visibility": "private", "codeMaker": "computer"}` and
    # stores the result in `comparable` for later use.
    comparable = config.to_dict() | {"visibility": "private", "codeMaker": "computer"}
    # Iterates through `name, preset in PRESETS.items()` for the nested operation.
    for name, preset in PRESETS.items():
        # Computes `preset.to_dict() | {"visibility": "private", "codeMaker": "computer"}` and
        # stores the result in `candidate` for later use.
        candidate = preset.to_dict() | {"visibility": "private", "codeMaker": "computer"}
        # Tests `comparable == candidate` before running the nested branch.
        if comparable == candidate:
            # Returns `name` to the caller as this function's result.
            return name
    # Returns `None` to the caller as this function's result.
    return None
