from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class APIError(Exception):
    status_code: int
    code: str
    message: str
    headers: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message
