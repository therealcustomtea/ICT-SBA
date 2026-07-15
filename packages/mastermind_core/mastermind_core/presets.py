from __future__ import annotations

from .errors import DomainError
from .models import COLOUR_IDS, GameConfig

PRESETS: dict[str, GameConfig] = {
    "easy": GameConfig(COLOUR_IDS[:5], 4, 12, False, ranked=True),
    "normal": GameConfig(COLOUR_IDS[:6], 4, 10, True, ranked=True),
    "hard": GameConfig(COLOUR_IDS[:8], 5, 8, True, ranked=True),
    "expert": GameConfig(COLOUR_IDS, 6, 8, True, ranked=True),
}


def get_preset(name: str) -> GameConfig:
    try:
        return PRESETS[name.strip().lower()]
    except KeyError as exc:
        raise DomainError(
            "UNKNOWN_DIFFICULTY", "Difficulty must be easy, normal, hard, or expert."
        ) from exc


def preset_name(config: GameConfig) -> str | None:
    comparable = config.to_dict() | {"visibility": "private", "codeMaker": "computer"}
    for name, preset in PRESETS.items():
        candidate = preset.to_dict() | {"visibility": "private", "codeMaker": "computer"}
        if comparable == candidate:
            return name
    return None
