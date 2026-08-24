# ruff: noqa: I001 -- line explanations intentionally separate imports.
# Adds the `Submission entry point for CHAN YU SHING's Mastermind game.` string to the
# surrounding call or ordered collection.
"""Submission entry point for CHAN YU SHING's Mastermind game."""

# Imports selected names from `mastermind_cli.__main__` for use in this module.
from mastermind_cli.__main__ import main


# Runs the following entry-point block only when this file is executed directly.
if __name__ == "__main__":
    # Raises the specified exception to report an invalid or failed operation.
    raise SystemExit(main())
