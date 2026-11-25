# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

# Imports selected names from `.app` for use in this module.
from .app import MastermindCLI


# Defines the `main` function and begins its typed parameter list.
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cipherboard local and online terminal client")
    parser.add_argument("--online", action="store_true", help="Open the complete online menu")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="Cipherboard API origin")
    parser.add_argument(
        "--product-origin",
        default="http://127.0.0.1:3000",
        help="GUI origin used by room authorization",
    )
    parser.add_argument(
        "--state-dir", type=Path, help="Parent directory for private per-server session files"
    )
    parser.add_argument(
        "--allow-http", action="store_true", help="Permit unencrypted HTTP on a trusted LAN"
    )
    parser.add_argument("--locale", choices=("en", "zh-Hant"), help="Online interface language")
    args = parser.parse_args(argv)
    online_status = 0

    def online() -> None:
        nonlocal online_status
        from .online import OnlineCLI
        from .online_client import OnlineClient, OnlineError

        try:
            client = OnlineClient(
                args.api_url,
                product_origin=args.product_origin,
                state_dir=args.state_dir,
                allow_http=args.allow_http,
            )
            try:
                OnlineCLI(client, locale=args.locale).run()
            finally:
                client.close()
        except OnlineError as exc:
            print(f"{exc.code}: {exc}")
            online_status = 1
        except (OSError, ValueError):
            print("Check the server origin and private CLI session file permissions.")
            online_status = 1

    # Starts a protected operation whose expected failures are handled below.
    try:
        # Returns `MastermindCLI().run()` to the caller as this function's result.
        if args.online:
            online()
            return online_status
        return MastermindCLI(online_fn=online, locale=args.locale or "en").run()
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
