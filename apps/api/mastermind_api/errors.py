# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import dataclass, field


# Applies `@dataclass(slots=True)` to configure the declaration immediately below.
@dataclass(slots=True)
# Defines the `APIError` class and its related behavior.
class APIError(Exception):
    # Declares the typed `status_code` data field.
    status_code: int
    # Declares the typed `code` data field.
    code: str
    # Declares the typed `message` data field.
    message: str
    # Computes and stores `headers` for subsequent operations.
    headers: dict[str, str] = field(default_factory=dict)

    # Defines the `__str__` callable and its typed interface.
    def __str__(self) -> str:
        # Returns this result to the caller and ends the current function.
        return self.message
