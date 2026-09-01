# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `pathlib` for use in this module.
from pathlib import Path

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_cli` for use in this module.
from mastermind_cli import CSVScoreStore, MastermindCLI

# Imports selected names from `mastermind_cli` for use in this module.
from mastermind_cli import __main__ as cli_main
from mastermind_cli.terminal import RESET, format_code, supports_colour


class FakeTerminal:
    def __init__(self, interactive: bool) -> None:
        self.interactive = interactive

    def isatty(self) -> bool:
        return self.interactive


# Defines the `ScriptedIO` class and its related behavior.
class ScriptedIO:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self, values: list[str]) -> None:
        # Computes and stores `self.values` for subsequent operations.
        self.values = iter(values)
        # Computes and stores `self.output` for subsequent operations.
        self.output: list[str] = []

    # Defines the `input` callable and its typed interface.
    def input(self, _prompt: str) -> str:
        # Returns this result to the caller and ends the current function.
        return next(self.values)

    # Defines the `print` callable and its typed interface.
    def print(self, value: str) -> None:
        # Calls `self.output.append` with the supplied values.
        self.output.append(value)


def test_terminal_colour_capability_respects_accessibility_and_stream_state() -> None:
    assert supports_colour(FakeTerminal(True), {}) is True
    assert supports_colour(FakeTerminal(False), {}) is False
    assert supports_colour(FakeTerminal(True), {"NO_COLOR": "1"}) is False
    assert supports_colour(FakeTerminal(True), {"TERM": "dumb"}) is False
    assert supports_colour(FakeTerminal(False), {"FORCE_COLOR": "1"}) is True


def test_colour_formatter_styles_each_identifier_without_changing_plain_fallback() -> None:
    identifiers = ("R", "B", "G", "Y", "W", "K", "O", "P", "C", "M")
    styled = format_code(identifiers, enabled=True)

    assert format_code(identifiers, enabled=False) == "R B G Y W K O P C M"
    assert styled.count(RESET) == len(identifiers)
    assert "\x1b[91mR\x1b[0m" in styled
    assert "\x1b[30;47mW\x1b[0m" in styled


def test_coloured_game_output_styles_palette_and_history_but_preserves_alignment(
    tmp_path: Path,
) -> None:
    io = ScriptedIO(["Ada", "5", "5", "3", "1", "y", "y", "RBG"])
    app = MastermindCLI(
        input_fn=io.input,
        secret_input_fn=lambda _prompt: "RBG",
        output_fn=io.print,
        colour_output=True,
        store=CSVScoreStore(tmp_path / "scores.csv"),
    )

    app.play_game()

    palette = next(line for line in io.output if line.startswith("Available colours:"))
    history = next(line for line in io.output if line.lstrip().startswith("1  \x1b"))
    assert "\x1b[91mR\x1b[0m" in palette
    assert "\x1b[94mB\x1b[0m" in palette
    assert "\x1b[92mG\x1b[0m" in history
    assert history.endswith("      3      0")


# Defines the `test_menu_handles_invalid_and_exit` callable and its typed interface.
def test_menu_handles_invalid_and_exit(tmp_path: Path) -> None:
    # Computes and stores `io` for subsequent operations.
    io = ScriptedIO(["nope", "5"])
    # Computes and stores `app` for subsequent operations.
    app = MastermindCLI(
        # Provides the `input_fn` parameter or keyword argument.
        input_fn=io.input,
        # Provides the `output_fn` parameter or keyword argument.
        output_fn=io.print,
        # Provides the `store` parameter or keyword argument.
        store=CSVScoreStore(tmp_path / "scores.csv"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert app.run() == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "Enter a number from 1 to 5." in io.output


# Defines the `test_abandoned_game_is_saved_with_zero_score` callable and its typed interface.
def test_abandoned_game_is_saved_with_zero_score(tmp_path: Path) -> None:
    # Computes and stores `io` for subsequent operations.
    io = ScriptedIO(["Player", "2", "quit"])
    # Computes and stores `store` for subsequent operations.
    store = CSVScoreStore(tmp_path / "scores.csv")
    # Computes and stores `app` for subsequent operations.
    app = MastermindCLI(input_fn=io.input, output_fn=io.print, store=store)
    # Calls `app.play_game` with the supplied values.
    app.play_game()
    # Computes and stores `saved` for subsequent operations.
    saved = store.read()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(saved) == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert saved[0].result == "abandoned"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert saved[0].score == 0


# Defines the `test_human_secret_is_obscured_and_each_valid_guess_shows_full_history` callable and
# its typed interface.
def test_human_secret_is_obscured_and_each_valid_guess_shows_full_history(
    # Declares the typed `tmp_path` data field.
    tmp_path: Path,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `io` for subsequent operations.
    io = ScriptedIO(["Ada", "5", "5", "3", "2", "y", "y", "RRR", "RBG"])
    # Computes and stores `secret_prompts` for subsequent operations.
    secret_prompts: list[str] = []

    # Defines the `secret_input` callable and its typed interface.
    def secret_input(prompt: str) -> str:
        # Calls `secret_prompts.append` with the supplied values.
        secret_prompts.append(prompt)
        # Returns this result to the caller and ends the current function.
        return "RBG"

    # Computes and stores `app` for subsequent operations.
    app = MastermindCLI(
        # Provides the `input_fn` parameter or keyword argument.
        input_fn=io.input,
        # Provides the `secret_input_fn` parameter or keyword argument.
        secret_input_fn=secret_input,
        # Provides the `output_fn` parameter or keyword argument.
        output_fn=io.print,
        # Provides the `store` parameter or keyword argument.
        store=CSVScoreStore(tmp_path / "scores.csv"),
        # Closes the multiline call, declaration, or collection started above.
    )

    # Calls `app.play_game` with the supplied values.
    app.play_game()

    # Asserts this invariant so an unexpected test state fails immediately.
    assert secret_prompts == ["Code Maker, enter the secret (input hidden): "]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert io.output.count("Attempt  Guess               Black  White") == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sum(line.lstrip().startswith("1  R R R") for line in io.output) == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sum(line.lstrip().startswith("2  R B G") for line in io.output) == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "1 attempt remaining." in io.output
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "0 attempts remaining." in io.output


# Defines the `test_save_failure_warns_without_ending_game` callable and its typed interface.
def test_save_failure_warns_without_ending_game(
    # Declares the typed `tmp_path` data field.
    tmp_path: Path,
    # Supplies this item to the surrounding call or collection.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `io` for subsequent operations.
    io = ScriptedIO(["Ada", "2", "quit"])
    # Computes and stores `store` for subsequent operations.
    store = CSVScoreStore(tmp_path / "scores.csv")

    # Defines the `fail_save` callable and its typed interface.
    def fail_save(_record: object) -> None:
        # Raises this exception to report an invalid or failed operation.
        raise OSError("disk unavailable")

    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(store, "append", fail_save)
    # Computes and stores `app` for subsequent operations.
    app = MastermindCLI(input_fn=io.input, output_fn=io.print, store=store)

    # Calls `app.play_game` with the supplied values.
    app.play_game()

    # Asserts this invariant so an unexpected test state fails immediately.
    assert "Warning: the result could not be saved (disk unavailable)." in io.output


# Defines the `test_export_failure_warns_and_returns_to_caller` callable and its typed interface.
def test_export_failure_warns_and_returns_to_caller(
    # Declares the typed `tmp_path` data field.
    tmp_path: Path,
    # Supplies this item to the surrounding call or collection.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `io` for subsequent operations.
    io = ScriptedIO(["copy.csv"])
    # Computes and stores `store` for subsequent operations.
    store = CSVScoreStore(tmp_path / "scores.csv")

    # Defines the `fail_export` callable and its typed interface.
    def fail_export(_destination: object) -> Path:
        # Raises this exception to report an invalid or failed operation.
        raise OSError("read-only destination")

    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(store, "export", fail_export)
    # Computes and stores `app` for subsequent operations.
    app = MastermindCLI(input_fn=io.input, output_fn=io.print, store=store)

    # Calls `app.export_scores` with the supplied values.
    app.export_scores()

    # Asserts this invariant so an unexpected test state fails immediately.
    assert "Warning: scores could not be exported (read-only destination)." in io.output


# Applies `@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt()])` to configure
# the declaration immediately below.
@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt()])
# Defines the `test_main_handles_interrupted_input_safely` callable and its typed interface.
def test_main_handles_interrupted_input_safely(
    # Declares the typed `exception` data field.
    exception: BaseException,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Declares the typed `capsys` data field.
    capsys: pytest.CaptureFixture[str],
    # Completes the signature and declares the callable return type.
) -> None:
    # Defines the `interrupt` callable and its typed interface.
    def interrupt(_app: MastermindCLI) -> int:
        # Raises this exception to report an invalid or failed operation.
        raise exception

    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(MastermindCLI, "run", interrupt)

    # Asserts this invariant so an unexpected test state fails immediately.
    assert cli_main.main() == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "Session ended safely." in capsys.readouterr().out
