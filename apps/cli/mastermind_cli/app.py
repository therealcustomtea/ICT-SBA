from __future__ import annotations

import csv
from collections.abc import Callable
from getpass import getpass
from pathlib import Path

from mastermind_core import (
    COLOUR_IDS,
    CodeMakerType,
    DomainError,
    GameConfig,
    GameMode,
    GameState,
    GameStatus,
    abandon_game,
    create_game,
    generate_secret,
    get_preset,
    submit_guess,
    validate_code,
)

from .storage import CSVScoreStore, ScoreRecord

Input = Callable[[str], str]
Output = Callable[[str], None]

RULES = """Mastermind rules
The Code Maker chooses a hidden sequence of coloured pegs.
Enter colour identifiers separated by spaces, commas, or hyphens.
A black peg means the right colour is in the right position.
A white peg means the right colour is in a different position.
Each secret peg can contribute at most one feedback peg.
Type quit during a game to abandon it."""


class MastermindCLI:
    def __init__(
        self,
        *,
        input_fn: Input = input,
        secret_input_fn: Input = getpass,
        output_fn: Output = print,
        store: CSVScoreStore | None = None,
    ) -> None:
        self.input = input_fn
        self.secret_input = secret_input_fn
        self.output = output_fn
        self.store = store or CSVScoreStore()

    def run(self) -> int:
        self.output("Mastermind Logic Lab")
        while True:
            self.output("\n1. Start game")
            self.output("2. View local high scores")
            self.output("3. View rules")
            self.output("4. Export scores")
            self.output("5. Exit")
            choice = self.input("Choose an option: ").strip()
            if choice == "1":
                self.play_game()
            elif choice == "2":
                self.show_scores()
            elif choice == "3":
                self.output(RULES)
            elif choice == "4":
                self.export_scores()
            elif choice == "5":
                self.output("Thanks for playing.")
                return 0
            else:
                self.output("Enter a number from 1 to 5.")

    def play_game(self) -> None:
        player_name = self.input("Player name: ").strip() or "Player"
        self.output("\n1. Easy  2. Normal  3. Hard  4. Expert  5. Custom")
        choice = self.input("Choose difficulty: ").strip()
        names = {"1": "easy", "2": "normal", "3": "hard", "4": "expert"}
        try:
            if choice in names:
                difficulty = names[choice]
                config = get_preset(difficulty)
            elif choice == "5":
                difficulty = "custom"
                config = self.custom_config()
            else:
                self.output("Enter a number from 1 to 5.")
                return
        except DomainError as exc:
            self.output(exc.message)
            return
        secret = self._choose_secret(config)
        state = create_game(
            config,
            GameMode.PASS_AND_PLAY if config.code_maker is CodeMakerType.HUMAN else GameMode.SOLO,
        )
        self.output(
            f"Available colours: {' '.join(config.colours)} | "
            f"Code length: {config.code_length} | Attempts: {config.max_attempts}"
        )
        while state.status is GameStatus.ACTIVE:
            raw = self.input(f"Guess ({state.attempts_remaining} remaining): ").strip()
            if raw.casefold() == "quit":
                state = abandon_game(state)
                break
            try:
                state = submit_guess(state, secret, raw)
            except DomainError as exc:
                self.output(exc.message)
                continue
            self._show_attempt_history(state)

        if state.status is GameStatus.WON:
            self.output(f"Code broken in {state.attempts_used} attempt(s)!")
        elif state.status is GameStatus.LOST:
            self.output(f"No attempts remain. The code was {' '.join(secret)}.")
        else:
            self.output("Game abandoned. No score was awarded.")
        score = state.score.total if state.score else 0
        self.output(f"Score: {score}")
        try:
            self.store.append(
                ScoreRecord.now(
                    player_name=player_name,
                    mode=state.mode.value,
                    difficulty=difficulty,
                    code_maker=config.code_maker.value,
                    number_of_colours=len(config.colours),
                    code_length=config.code_length,
                    duplicates_allowed=config.duplicates_allowed,
                    attempts_used=state.attempts_used,
                    maximum_attempts=config.max_attempts,
                    score=score,
                    scoring_version=state.score.version if state.score else "score_v1",
                    result=state.status.value,
                )
            )
        except (OSError, csv.Error, UnicodeError) as exc:
            self.output(f"Warning: the result could not be saved ({exc}).")

    def _show_attempt_history(self, state: GameState) -> None:
        self.output("Attempt  Guess               Black  White")
        for attempt in state.attempts:
            self.output(
                f"{attempt.number:>7}  {' '.join(attempt.guess):<18}  "
                f"{attempt.feedback.black:>5}  {attempt.feedback.white:>5}"
            )
        label = "attempt" if state.attempts_remaining == 1 else "attempts"
        self.output(f"{state.attempts_remaining} {label} remaining.")

    def custom_config(self) -> GameConfig:
        number_of_colours = self._number("Number of colours (5-10): ", 5, 10)
        code_length = self._number("Code length (3-6): ", 3, 6)
        attempts = self._number("Maximum attempts (1-20): ", 1, 20)
        duplicates = self._yes_no("Allow duplicate colours? (y/n): ")
        human = self._yes_no("Human Code Maker? (y/n): ")
        return GameConfig(
            colours=COLOUR_IDS[:number_of_colours],
            code_length=code_length,
            max_attempts=attempts,
            duplicates_allowed=duplicates,
            code_maker=CodeMakerType.HUMAN if human else CodeMakerType.COMPUTER,
            ranked=False,
        )

    def _choose_secret(self, config: GameConfig) -> tuple[str, ...]:
        if config.code_maker is CodeMakerType.COMPUTER:
            return generate_secret(config)
        while True:
            raw = self.secret_input("Code Maker, enter the secret (input hidden): ")
            try:
                secret = validate_code(raw, config)
                self.output("\n" * 40)
                self.output("Pass the device to the Code Breaker.")
                return secret
            except DomainError as exc:
                self.output(exc.message)

    def _number(self, prompt: str, minimum: int, maximum: int) -> int:
        while True:
            raw = self.input(prompt).strip()
            try:
                value = int(raw)
            except ValueError:
                self.output("Enter a whole number.")
                continue
            if minimum <= value <= maximum:
                return value
            self.output(f"Enter a number from {minimum} to {maximum}.")

    def _yes_no(self, prompt: str) -> bool:
        while True:
            raw = self.input(prompt).strip().casefold()
            if raw in {"y", "yes"}:
                return True
            if raw in {"n", "no"}:
                return False
            self.output("Enter y or n.")

    def show_scores(self) -> None:
        records = self.store.read()
        if not records:
            self.output("No local scores yet.")
            return
        self.output("Rank  Player                    Difficulty  Score  Attempts")
        for rank, record in enumerate(records[:20], start=1):
            self.output(
                f"{rank:>4}  {record.player_name[:24]:<24}  {record.difficulty:<10}  "
                f"{record.score:>5}  {record.attempts_used}/{record.maximum_attempts}"
            )

    def export_scores(self) -> None:
        destination = self.input("Export path [mastermind_scores.csv]: ").strip()
        try:
            path = self.store.export(Path(destination or "mastermind_scores.csv"))
        except (OSError, csv.Error, UnicodeError) as exc:
            self.output(f"Warning: scores could not be exported ({exc}).")
            return
        self.output(f"Scores exported to {path}.")
