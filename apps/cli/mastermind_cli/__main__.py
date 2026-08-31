# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports selected names from `.app` for use in this module.
from .app import MastermindCLI


# Defines the `main` function and begins its typed parameter list.
def main() -> int:
    # Starts a protected operation whose expected failures are handled below.
    try:
        # Returns `MastermindCLI().run()` to the caller as this function's result.
        return MastermindCLI().run()
    # Handles the listed exception types so the program can recover safely.
    except (EOFError, KeyboardInterrupt):
        # Prints this fallback message to the terminal for the current user.
        print("\nSession ended safely.")
        # Returns `0` to the caller as this function's result.
        return 0


# Runs the following entry-point block only when this file is executed directly.
if __name__ == "__main__":
    # Raises the specified exception to report an invalid or failed operation.
    raise SystemExit(main())
