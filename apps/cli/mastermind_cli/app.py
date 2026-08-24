# ruff: noqa: I001 -- line explanations intentionally separate imports.
# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports `csv` so its functionality is available below.
import csv
# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Callable
# Imports selected names from `getpass` for use in this module.
from getpass import getpass
# Imports selected names from `pathlib` for use in this module.
from pathlib import Path

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import (
    # Includes `COLOUR_IDS` in the surrounding import, call, or collection.
    COLOUR_IDS,
    # Includes `CodeMakerType` in the surrounding import, call, or collection.
    CodeMakerType,
    # Includes `DomainError` in the surrounding import, call, or collection.
    DomainError,
    # Includes `GameConfig` in the surrounding import, call, or collection.
    GameConfig,
    # Includes `GameMode` in the surrounding import, call, or collection.
    GameMode,
    # Includes `GameState` in the surrounding import, call, or collection.
    GameState,
    # Includes `GameStatus` in the surrounding import, call, or collection.
    GameStatus,
    # Includes `abandon_game` in the surrounding import, call, or collection.
    abandon_game,
    # Includes `create_game` in the surrounding import, call, or collection.
    create_game,
    # Includes `generate_secret` in the surrounding import, call, or collection.
    generate_secret,
    # Includes `get_preset` in the surrounding import, call, or collection.
    get_preset,
    # Includes `submit_guess` in the surrounding import, call, or collection.
    submit_guess,
    # Includes `validate_code` in the surrounding import, call, or collection.
    validate_code,
# Closes the multiline call or collection started on an earlier line.
)

# Imports selected names from `.storage` for use in this module.
from .storage import CSVScoreStore, ScoreRecord

# Computes `Callable[[str], str]` and stores the result in `Input` for later use.
Input = Callable[[str], str]
# Computes `Callable[[str], None]` and stores the result in `Output` for later use.
Output = Callable[[str], None]

# Defines the multiline game instructions displayed by the rules menu.
RULES = """Mastermind rules
The Code Maker chooses a hidden sequence of coloured pegs.
Enter colour identifiers separated by spaces, commas, or hyphens.
A black peg means the right colour is in the right position.
A white peg means the right colour is in a different position.
Each secret peg can contribute at most one feedback peg.
Type quit during a game to abandon it."""


# Defines the `MastermindCLI` type used to group related data and behavior.
class MastermindCLI:
    # Defines the `__init__` function and begins its typed parameter list.
    def __init__(
        # Declares the current object as the instance received by this method.
        self,
        # Makes all following function parameters keyword-only for clearer call sites.
        *,
        # Provides `input` as the `input_fn` parameter or argument.
        input_fn: Input = input,
        # Provides `getpass` as the `secret_input_fn` parameter or argument.
        secret_input_fn: Input = getpass,
        # Provides `print` as the `output_fn` parameter or argument.
        output_fn: Output = print,
        # Provides `None` as the `store` parameter or argument.
        store: CSVScoreStore | None = None,
    # Completes the function signature and declares the type returned to callers.
    ) -> None:
        # Stores `input_fn` on this instance as `self.input` for later method calls.
        self.input = input_fn
        # Stores `secret_input_fn` on this instance as `self.secret_input` for later method
        # calls.
        self.secret_input = secret_input_fn
        # Stores `output_fn` on this instance as `self.output` for later method calls.
        self.output = output_fn
        # Stores `store or CSVScoreStore()` on this instance as `self.store` for later method
        # calls.
        self.store = store or CSVScoreStore()

    # Defines the `run` function and begins its typed parameter list.
    def run(self) -> int:
        # Sends this user-facing message through the configured output function.
        self.output("Mastermind Logic Lab")
        # Repeats the nested block while `True` remains true.
        while True:
            # Sends this user-facing message through the configured output function.
            self.output("\n1. Start game")
            # Sends this user-facing message through the configured output function.
            self.output("2. View local high scores")
            # Sends this user-facing message through the configured output function.
            self.output("3. View rules")
            # Sends this user-facing message through the configured output function.
            self.output("4. Export scores")
            # Sends this user-facing message through the configured output function.
            self.output("5. Exit")
            # Computes `self.input("Choose an option: ").strip()` and stores the result in
            # `choice` for later use.
            choice = self.input("Choose an option: ").strip()
            # Tests `choice == "1"` before running the nested branch.
            if choice == "1":
                # Calls `self.play_game` to perform this step with the supplied arguments.
                self.play_game()
            # Tests the next condition when earlier branches did not run.
            elif choice == "2":
                # Calls `self.show_scores` to perform this step with the supplied arguments.
                self.show_scores()
            # Tests the next condition when earlier branches did not run.
            elif choice == "3":
                # Sends this user-facing message through the configured output function.
                self.output(RULES)
            # Tests the next condition when earlier branches did not run.
            elif choice == "4":
                # Calls `self.export_scores` to perform this step with the supplied arguments.
                self.export_scores()
            # Tests the next condition when earlier branches did not run.
            elif choice == "5":
                # Sends this user-facing message through the configured output function.
                self.output("Thanks for playing.")
                # Returns `0` to the caller as this function's result.
                return 0
            # Handles the remaining case when the preceding conditions were false.
            else:
                # Sends this user-facing message through the configured output function.
                self.output("Enter a number from 1 to 5.")

    # Defines the `play_game` function and begins its typed parameter list.
    def play_game(self) -> None:
        # Computes `self.input("Player name: ").strip() or "Player"` and stores the result in
        # `player_name` for later use.
        player_name = self.input("Player name: ").strip() or "Player"
        # Sends this user-facing message through the configured output function.
        self.output("\n1. Easy  2. Normal  3. Hard  4. Expert  5. Custom")
        # Computes `self.input("Choose difficulty: ").strip()` and stores the result in `choice`
        # for later use.
        choice = self.input("Choose difficulty: ").strip()
        # Computes `{"1": "easy", "2": "normal", "3": "hard", "4": "expert"}` and stores the
        # result in `names` for later use.
        names = {"1": "easy", "2": "normal", "3": "hard", "4": "expert"}
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Tests `choice in names` before running the nested branch.
            if choice in names:
                # Computes `names[choice]` and stores the result in `difficulty` for later use.
                difficulty = names[choice]
                # Computes `get_preset(difficulty)` and stores the result in `config` for later
                # use.
                config = get_preset(difficulty)
            # Tests the next condition when earlier branches did not run.
            elif choice == "5":
                # Computes `"custom"` and stores the result in `difficulty` for later use.
                difficulty = "custom"
                # Computes `self.custom_config()` and stores the result in `config` for later
                # use.
                config = self.custom_config()
            # Handles the remaining case when the preceding conditions were false.
            else:
                # Sends this user-facing message through the configured output function.
                self.output("Enter a number from 1 to 5.")
                # Ends this function immediately and returns no value to its caller.
                return
        # Handles the listed exception types so the program can recover safely.
        except DomainError as exc:
            # Sends this user-facing message through the configured output function.
            self.output(exc.message)
            # Ends this function immediately and returns no value to its caller.
            return
        # Computes `self._choose_secret(config)` and stores the result in `secret` for later
        # use.
        secret = self._choose_secret(config)
        # Computes `create_game(` and stores the result in `state` for later use.
        state = create_game(
            # Includes `config` in the surrounding import, call, or collection.
            config,
            # Supplies this value to the surrounding multiline call or collection.
            GameMode.PASS_AND_PLAY if config.code_maker is CodeMakerType.HUMAN else GameMode.SOLO,
        # Closes the multiline call or collection started on an earlier line.
        )
        # Sends this user-facing message through the configured output function.
        self.output(
            # Adds this formatted text segment to the message being constructed.
            f"Available colours: {' '.join(config.colours)} | "
            # Adds this formatted text segment to the message being constructed.
            f"Code length: {config.code_length} | Attempts: {config.max_attempts}"
        # Closes the multiline call or collection started on an earlier line.
        )
        # Repeats the nested block while `state.status is GameStatus.ACTIVE` remains true.
        while state.status is GameStatus.ACTIVE:
            # Computes `self.input(f"Guess ({state.attempts_remaining} remaining): ").strip()`
            # and stores the result in `raw` for later use.
            raw = self.input(f"Guess ({state.attempts_remaining} remaining): ").strip()
            # Tests `raw.casefold() == "quit"` before running the nested branch.
            if raw.casefold() == "quit":
                # Computes `abandon_game(state)` and stores the result in `state` for later use.
                state = abandon_game(state)
                # Stops the nearest loop because its terminating condition has been reached.
                break
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Computes `submit_guess(state, secret, raw)` and stores the result in `state`
                # for later use.
                state = submit_guess(state, secret, raw)
            # Handles the listed exception types so the program can recover safely.
            except DomainError as exc:
                # Sends this user-facing message through the configured output function.
                self.output(exc.message)
                # Skips the rest of this iteration and starts the next loop iteration.
                continue
            # Calls `self._show_attempt_history` to perform this step with the supplied
            # arguments.
            self._show_attempt_history(state)

        # Tests `state.status is GameStatus.WON` before running the nested branch.
        if state.status is GameStatus.WON:
            # Sends this user-facing message through the configured output function.
            self.output(f"Code broken in {state.attempts_used} attempt(s)!")
        # Tests the next condition when earlier branches did not run.
        elif state.status is GameStatus.LOST:
            # Sends this user-facing message through the configured output function.
            self.output(f"No attempts remain. The code was {' '.join(secret)}.")
        # Handles the remaining case when the preceding conditions were false.
        else:
            # Sends this user-facing message through the configured output function.
            self.output("Game abandoned. No score was awarded.")
        # Computes `state.score.total if state.score else 0` and stores the result in `score`
        # for later use.
        score = state.score.total if state.score else 0
        # Sends this user-facing message through the configured output function.
        self.output(f"Score: {score}")
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Starts a multiline function call whose arguments are supplied below.
            self.store.append(
                # Starts a multiline function call whose arguments are supplied below.
                ScoreRecord.now(
                    # Provides `player_name` as the `player_name` parameter or argument.
                    player_name=player_name,
                    # Provides `state.mode.value` as the `mode` parameter or argument.
                    mode=state.mode.value,
                    # Provides `difficulty` as the `difficulty` parameter or argument.
                    difficulty=difficulty,
                    # Provides `config.code_maker.value` as the `code_maker` parameter or
                    # argument.
                    code_maker=config.code_maker.value,
                    # Provides `len(config.colours)` as the `number_of_colours` parameter or
                    # argument.
                    number_of_colours=len(config.colours),
                    # Provides `config.code_length` as the `code_length` parameter or argument.
                    code_length=config.code_length,
                    # Provides `config.duplicates_allowed` as the `duplicates_allowed` parameter
                    # or argument.
                    duplicates_allowed=config.duplicates_allowed,
                    # Provides `state.attempts_used` as the `attempts_used` parameter or
                    # argument.
                    attempts_used=state.attempts_used,
                    # Provides `config.max_attempts` as the `maximum_attempts` parameter or
                    # argument.
                    maximum_attempts=config.max_attempts,
                    # Provides `score` as the `score` parameter or argument.
                    score=score,
                    # Provides `state.score.version if state.score else "score_v1"` as the
                    # `scoring_version` parameter or argument.
                    scoring_version=state.score.version if state.score else "score_v1",
                    # Provides `state.status.value` as the `result` parameter or argument.
                    result=state.status.value,
                # Closes the multiline call or collection started on an earlier line.
                )
            # Closes the multiline call or collection started on an earlier line.
            )
        # Handles the listed exception types so the program can recover safely.
        except (OSError, csv.Error, UnicodeError) as exc:
            # Sends this user-facing message through the configured output function.
            self.output(f"Warning: the result could not be saved ({exc}).")

    # Defines the `_show_attempt_history` function and begins its typed parameter list.
    def _show_attempt_history(self, state: GameState) -> None:
        # Sends this user-facing message through the configured output function.
        self.output("Attempt  Guess               Black  White")
        # Iterates through `attempt in state.attempts` for the nested operation.
        for attempt in state.attempts:
            # Sends this user-facing message through the configured output function.
            self.output(
                # Adds this formatted text segment to the message being constructed.
                f"{attempt.number:>7}  {' '.join(attempt.guess):<18}  "
                # Adds this formatted text segment to the message being constructed.
                f"{attempt.feedback.black:>5}  {attempt.feedback.white:>5}"
            # Closes the multiline call or collection started on an earlier line.
            )
        # Continues the surrounding expression or executes the next required operation.
        label = "attempt" if state.attempts_remaining == 1 else "attempts"
        # Sends this user-facing message through the configured output function.
        self.output(f"{state.attempts_remaining} {label} remaining.")

    # Defines the `custom_config` function and begins its typed parameter list.
    def custom_config(self) -> GameConfig:
        # Computes `self._number("Number of colours (5-10): ", 5, 10)` and stores the result in
        # `number_of_colours` for later use.
        number_of_colours = self._number("Number of colours (5-10): ", 5, 10)
        # Computes `self._number("Code length (3-6): ", 3, 6)` and stores the result in
        # `code_length` for later use.
        code_length = self._number("Code length (3-6): ", 3, 6)
        # Computes `self._number("Maximum attempts (1-20): ", 1, 20)` and stores the result in
        # `attempts` for later use.
        attempts = self._number("Maximum attempts (1-20): ", 1, 20)
        # Computes `self._yes_no("Allow duplicate colours? (y/n): ")` and stores the result in
        # `duplicates` for later use.
        duplicates = self._yes_no("Allow duplicate colours? (y/n): ")
        # Computes `self._yes_no("Human Code Maker? (y/n): ")` and stores the result in `human`
        # for later use.
        human = self._yes_no("Human Code Maker? (y/n): ")
        # Begins constructing the value that this function returns to its caller.
        return GameConfig(
            # Provides `COLOUR_IDS[:number_of_colours]` as the `colours` parameter or argument.
            colours=COLOUR_IDS[:number_of_colours],
            # Provides `code_length` as the `code_length` parameter or argument.
            code_length=code_length,
            # Provides `attempts` as the `max_attempts` parameter or argument.
            max_attempts=attempts,
            # Provides `duplicates` as the `duplicates_allowed` parameter or argument.
            duplicates_allowed=duplicates,
            # Provides `CodeMakerType.HUMAN if human else CodeMakerType.COMPUTER` as the
            # `code_maker` parameter or argument.
            code_maker=CodeMakerType.HUMAN if human else CodeMakerType.COMPUTER,
            # Provides `False` as the `ranked` parameter or argument.
            ranked=False,
        # Closes the multiline call or collection started on an earlier line.
        )

    # Defines the `_choose_secret` function and begins its typed parameter list.
    def _choose_secret(self, config: GameConfig) -> tuple[str, ...]:
        # Tests `config.code_maker is CodeMakerType.COMPUTER` before running the nested branch.
        if config.code_maker is CodeMakerType.COMPUTER:
            # Returns `generate_secret(config)` to the caller as this function's result.
            return generate_secret(config)
        # Repeats the nested block while `True` remains true.
        while True:
            # Computes `self.secret_input("Code Maker, enter the secret (input hidden): ")` and
            # stores the result in `raw` for later use.
            raw = self.secret_input("Code Maker, enter the secret (input hidden): ")
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Computes `validate_code(raw, config)` and stores the result in `secret` for
                # later use.
                secret = validate_code(raw, config)
                # Sends this user-facing message through the configured output function.
                self.output("\n" * 40)
                # Sends this user-facing message through the configured output function.
                self.output("Pass the device to the Code Breaker.")
                # Returns `secret` to the caller as this function's result.
                return secret
            # Handles the listed exception types so the program can recover safely.
            except DomainError as exc:
                # Sends this user-facing message through the configured output function.
                self.output(exc.message)

    # Defines the `_number` function and begins its typed parameter list.
    def _number(self, prompt: str, minimum: int, maximum: int) -> int:
        # Repeats the nested block while `True` remains true.
        while True:
            # Computes `self.input(prompt).strip()` and stores the result in `raw` for later
            # use.
            raw = self.input(prompt).strip()
            # Starts a protected operation whose expected failures are handled below.
            try:
                # Computes `int(raw)` and stores the result in `value` for later use.
                value = int(raw)
            # Handles the listed exception types so the program can recover safely.
            except ValueError:
                # Sends this user-facing message through the configured output function.
                self.output("Enter a whole number.")
                # Skips the rest of this iteration and starts the next loop iteration.
                continue
            # Tests `minimum <= value <= maximum` before running the nested branch.
            if minimum <= value <= maximum:
                # Returns `value` to the caller as this function's result.
                return value
            # Sends this user-facing message through the configured output function.
            self.output(f"Enter a number from {minimum} to {maximum}.")

    # Defines the `_yes_no` function and begins its typed parameter list.
    def _yes_no(self, prompt: str) -> bool:
        # Repeats the nested block while `True` remains true.
        while True:
            # Computes `self.input(prompt).strip().casefold()` and stores the result in `raw`
            # for later use.
            raw = self.input(prompt).strip().casefold()
            # Tests `raw in {"y", "yes"}` before running the nested branch.
            if raw in {"y", "yes"}:
                # Returns `True` to the caller as this function's result.
                return True
            # Tests `raw in {"n", "no"}` before running the nested branch.
            if raw in {"n", "no"}:
                # Returns `False` to the caller as this function's result.
                return False
            # Sends this user-facing message through the configured output function.
            self.output("Enter y or n.")

    # Defines the `show_scores` function and begins its typed parameter list.
    def show_scores(self) -> None:
        # Computes `self.store.read()` and stores the result in `records` for later use.
        records = self.store.read()
        # Tests `not records` before running the nested branch.
        if not records:
            # Sends this user-facing message through the configured output function.
            self.output("No local scores yet.")
            # Ends this function immediately and returns no value to its caller.
            return
        # Sends this user-facing message through the configured output function.
        self.output("Rank  Player                    Difficulty  Score  Attempts")
        # Iterates through `rank, record in enumerate(records[:20], start=1)` for the nested
        # operation.
        for rank, record in enumerate(records[:20], start=1):
            # Sends this user-facing message through the configured output function.
            self.output(
                # Adds this formatted text segment to the message being constructed.
                f"{rank:>4}  {record.player_name[:24]:<24}  {record.difficulty:<10}  "
                # Adds this formatted text segment to the message being constructed.
                f"{record.score:>5}  {record.attempts_used}/{record.maximum_attempts}"
            # Closes the multiline call or collection started on an earlier line.
            )

    # Defines the `export_scores` function and begins its typed parameter list.
    def export_scores(self) -> None:
        # Computes `self.input("Export path [mastermind_scores.csv]: ").strip()` and stores the
        # result in `destination` for later use.
        destination = self.input("Export path [mastermind_scores.csv]: ").strip()
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Computes `self.store.export(Path(destination or "mastermind_scores.csv"))` and
            # stores the result in `path` for later use.
            path = self.store.export(Path(destination or "mastermind_scores.csv"))
        # Handles the listed exception types so the program can recover safely.
        except (OSError, csv.Error, UnicodeError) as exc:
            # Sends this user-facing message through the configured output function.
            self.output(f"Warning: scores could not be exported ({exc}).")
            # Ends this function immediately and returns no value to its caller.
            return
        # Sends this user-facing message through the configured output function.
        self.output(f"Scores exported to {path}.")
