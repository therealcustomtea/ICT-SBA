from __future__ import annotations

from pathlib import Path

import pytest
from mastermind_cli import CSVScoreStore, MastermindCLI
from mastermind_cli import __main__ as cli_main


class ScriptedIO:
    def __init__(self, values: list[str]) -> None:
        self.values = iter(values)
        self.output: list[str] = []

    def input(self, _prompt: str) -> str:
        return next(self.values)

    def print(self, value: str) -> None:
        self.output.append(value)


def test_menu_handles_invalid_and_exit(tmp_path: Path) -> None:
    io = ScriptedIO(["nope", "5"])
    app = MastermindCLI(
        input_fn=io.input,
        output_fn=io.print,
        store=CSVScoreStore(tmp_path / "scores.csv"),
    )
    assert app.run() == 0
    assert "Enter a number from 1 to 5." in io.output


def test_abandoned_game_is_saved_with_zero_score(tmp_path: Path) -> None:
    io = ScriptedIO(["Player", "2", "quit"])
    store = CSVScoreStore(tmp_path / "scores.csv")
    app = MastermindCLI(input_fn=io.input, output_fn=io.print, store=store)
    app.play_game()
    saved = store.read()
    assert len(saved) == 1
    assert saved[0].result == "abandoned"
    assert saved[0].score == 0


def test_human_secret_is_obscured_and_each_valid_guess_shows_full_history(
    tmp_path: Path,
) -> None:
    io = ScriptedIO(["Ada", "5", "5", "3", "2", "y", "y", "RRR", "RBG"])
    secret_prompts: list[str] = []

    def secret_input(prompt: str) -> str:
        secret_prompts.append(prompt)
        return "RBG"

    app = MastermindCLI(
        input_fn=io.input,
        secret_input_fn=secret_input,
        output_fn=io.print,
        store=CSVScoreStore(tmp_path / "scores.csv"),
    )

    app.play_game()

    assert secret_prompts == ["Code Maker, enter the secret (input hidden): "]
    assert io.output.count("Attempt  Guess               Black  White") == 2
    assert sum(line.lstrip().startswith("1  R R R") for line in io.output) == 2
    assert sum(line.lstrip().startswith("2  R B G") for line in io.output) == 1
    assert "1 attempt remaining." in io.output
    assert "0 attempts remaining." in io.output


def test_save_failure_warns_without_ending_game(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    io = ScriptedIO(["Ada", "2", "quit"])
    store = CSVScoreStore(tmp_path / "scores.csv")

    def fail_save(_record: object) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(store, "append", fail_save)
    app = MastermindCLI(input_fn=io.input, output_fn=io.print, store=store)

    app.play_game()

    assert "Warning: the result could not be saved (disk unavailable)." in io.output


def test_export_failure_warns_and_returns_to_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    io = ScriptedIO(["copy.csv"])
    store = CSVScoreStore(tmp_path / "scores.csv")

    def fail_export(_destination: object) -> Path:
        raise OSError("read-only destination")

    monkeypatch.setattr(store, "export", fail_export)
    app = MastermindCLI(input_fn=io.input, output_fn=io.print, store=store)

    app.export_scores()

    assert "Warning: scores could not be exported (read-only destination)." in io.output


@pytest.mark.parametrize("exception", [EOFError(), KeyboardInterrupt()])
def test_main_handles_interrupted_input_safely(
    exception: BaseException,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def interrupt(_app: MastermindCLI) -> int:
        raise exception

    monkeypatch.setattr(MastermindCLI, "run", interrupt)

    assert cli_main.main() == 0
    assert "Session ended safely." in capsys.readouterr().out
