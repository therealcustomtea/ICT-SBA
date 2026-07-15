from __future__ import annotations

from .app import MastermindCLI


def main() -> int:
    try:
        return MastermindCLI().run()
    except (EOFError, KeyboardInterrupt):
        print("\nSession ended safely.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
