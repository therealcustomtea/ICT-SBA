# Defers annotation evaluation so modern type hints work without runtime lookups.
from __future__ import annotations

# Imports `csv` so its functionality is available below.
import csv

# Imports `os` so its functionality is available below.
import os

# Imports `tempfile` so its functionality is available below.
import tempfile

# Imports `warnings` so its functionality is available below.
import warnings

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import asdict, dataclass

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime

# Imports selected names from `pathlib` for use in this module.
from pathlib import Path

# Assigns `(` to the named `CSV_FIELDS` constant used by the application.
CSV_FIELDS = (
    # Adds the `timestamp` string to the surrounding call or ordered collection.
    "timestamp",
    # Adds the `player_name` string to the surrounding call or ordered collection.
    "player_name",
    # Adds the `mode` string to the surrounding call or ordered collection.
    "mode",
    # Adds the `difficulty` string to the surrounding call or ordered collection.
    "difficulty",
    # Adds the `code_maker` string to the surrounding call or ordered collection.
    "code_maker",
    # Adds the `number_of_colours` string to the surrounding call or ordered collection.
    "number_of_colours",
    # Adds the `code_length` string to the surrounding call or ordered collection.
    "code_length",
    # Adds the `duplicates_allowed` string to the surrounding call or ordered collection.
    "duplicates_allowed",
    # Adds the `attempts_used` string to the surrounding call or ordered collection.
    "attempts_used",
    # Adds the `maximum_attempts` string to the surrounding call or ordered collection.
    "maximum_attempts",
    # Adds the `score` string to the surrounding call or ordered collection.
    "score",
    # Adds the `scoring_version` string to the surrounding call or ordered collection.
    "scoring_version",
    # Adds the `result` string to the surrounding call or ordered collection.
    "result",
    # Closes the multiline call or collection started on an earlier line.
)


# Defines the `csv_safe` function and begins its typed parameter list.
def csv_safe(value: object) -> str:
    # Computes `str(value)` and stores the result in `text` for later use.
    text = str(value)
    # Returns `f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text` to the
    # caller as this function's result.
    return f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


# Applies `@dataclass(frozen=True, slots=True)` to configure the class or method declared
# immediately below.
@dataclass(frozen=True, slots=True)
# Defines the `ScoreRecord` type used to group related data and behavior.
class ScoreRecord:
    # Declares `timestamp` as `str` so the data shape is explicit.
    timestamp: str
    # Declares `player_name` as `str` so the data shape is explicit.
    player_name: str
    # Declares `mode` as `str` so the data shape is explicit.
    mode: str
    # Declares `difficulty` as `str` so the data shape is explicit.
    difficulty: str
    # Declares `code_maker` as `str` so the data shape is explicit.
    code_maker: str
    # Declares `number_of_colours` as `int` so the data shape is explicit.
    number_of_colours: int
    # Declares `code_length` as `int` so the data shape is explicit.
    code_length: int
    # Declares `duplicates_allowed` as `bool` so the data shape is explicit.
    duplicates_allowed: bool
    # Declares `attempts_used` as `int` so the data shape is explicit.
    attempts_used: int
    # Declares `maximum_attempts` as `int` so the data shape is explicit.
    maximum_attempts: int
    # Declares `score` as `int` so the data shape is explicit.
    score: int
    # Declares `scoring_version` as `str` so the data shape is explicit.
    scoring_version: str
    # Declares `result` as `str` so the data shape is explicit.
    result: str

    # Applies `@classmethod` to configure the class or method declared immediately below.
    @classmethod
    # Defines the `now` function and begins its typed parameter list.
    def now(cls, **values: object) -> ScoreRecord:
        # Returns `cls(timestamp=datetime.now(UTC).isoformat(), **values)  # type: ignore[arg-
        # type]` to the caller as this function's result.
        return cls(timestamp=datetime.now(UTC).isoformat(), **values)  # type: ignore[arg-type]


# Defines the `CSVScoreStore` type used to group related data and behavior.
class CSVScoreStore:
    # Defines the `__init__` function and begins its typed parameter list.
    def __init__(self, path: Path | str = Path("data/high_scores.csv")) -> None:
        # Stores `Path(path)` on this instance as `self.path` for later method calls.
        self.path = Path(path)

    # Defines the `append` function and begins its typed parameter list.
    def append(self, record: ScoreRecord) -> None:
        # Calls `self.path.parent.mkdir` to perform this step with the supplied arguments.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Continues the surrounding expression or executes the next required operation.
        needs_header = not self.path.exists() or self.path.stat().st_size == 0
        # Opens a managed resource and guarantees it is closed after the nested block.
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            # Computes `csv.DictWriter(handle, fieldnames=CSV_FIELDS)` and stores the result in
            # `writer` for later use.
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            # Tests `needs_header` before running the nested branch.
            if needs_header:
                # Uses the CSV writer to persist this header or record in the open file.
                writer.writeheader()
            # Uses the CSV writer to persist this header or record in the open file.
            writer.writerow({key: csv_safe(value) for key, value in asdict(record).items()})
            # Flushes buffered file data or exposes its descriptor for durable storage.
            handle.flush()
            # Forces buffered file contents to disk before reporting the write as complete.
            os.fsync(handle.fileno())

    # Defines the `read` function and begins its typed parameter list.
    def read(self) -> list[ScoreRecord]:
        # Tests `not self.path.exists()` before running the nested branch.
        if not self.path.exists():
            # Returns `[]` to the caller as this function's result.
            return []
        # Computes `[]` and stores the result in `records` for later use.
        records: list[ScoreRecord] = []
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Opens a managed resource and guarantees it is closed after the nested block.
            with self.path.open(encoding="utf-8", newline="") as handle:
                # Computes `csv.DictReader(handle)` and stores the result in `reader` for later
                # use.
                reader = csv.DictReader(handle)
                # Tests `not reader.fieldnames or not
                # set(CSV_FIELDS).issubset(reader.fieldnames)` before running the nested branch.
                if not reader.fieldnames or not set(CSV_FIELDS).issubset(reader.fieldnames):
                    # Emits a runtime warning so malformed or unreadable stored data is visible.
                    warnings.warn(
                        # Adds this formatted text segment to the message being constructed.
                        f"Ignored {self.path}: the score file header is malformed.",
                        # Includes `RuntimeWarning` in the surrounding import, call, or
                        # collection.
                        RuntimeWarning,
                        # Provides `2` as the `stacklevel` parameter or argument.
                        stacklevel=2,
                        # Closes the multiline call or collection started on an earlier line.
                    )
                    # Returns `[]` to the caller as this function's result.
                    return []
                # Iterates through `row in reader` for the nested operation.
                for row in reader:
                    # Starts a protected operation whose expected failures are handled below.
                    try:
                        # Adds a validated score record to the in-memory result collection.
                        records.append(
                            # Starts a multiline function call whose arguments are supplied
                            # below.
                            ScoreRecord(
                                # Provides `row["timestamp"]` as the `timestamp` parameter or
                                # argument.
                                timestamp=row["timestamp"],
                                # Provides `row["player_name"]` as the `player_name` parameter
                                # or argument.
                                player_name=row["player_name"],
                                # Provides `row["mode"]` as the `mode` parameter or argument.
                                mode=row["mode"],
                                # Provides `row["difficulty"]` as the `difficulty` parameter or
                                # argument.
                                difficulty=row["difficulty"],
                                # Provides `row["code_maker"]` as the `code_maker` parameter or
                                # argument.
                                code_maker=row["code_maker"],
                                # Provides `int(row["number_of_colours"])` as the
                                # `number_of_colours` parameter or argument.
                                number_of_colours=int(row["number_of_colours"]),
                                # Provides `int(row["code_length"])` as the `code_length`
                                # parameter or argument.
                                code_length=int(row["code_length"]),
                                # Provides `row["duplicates_allowed"].casefold() == "true"` as
                                # the `duplicates_allowed` parameter or argument.
                                duplicates_allowed=row["duplicates_allowed"].casefold() == "true",
                                # Provides `int(row["attempts_used"])` as the `attempts_used`
                                # parameter or argument.
                                attempts_used=int(row["attempts_used"]),
                                # Provides `int(row["maximum_attempts"])` as the
                                # `maximum_attempts` parameter or argument.
                                maximum_attempts=int(row["maximum_attempts"]),
                                # Provides `int(row["score"])` as the `score` parameter or
                                # argument.
                                score=int(row["score"]),
                                # Provides `row["scoring_version"]` as the `scoring_version`
                                # parameter or argument.
                                scoring_version=row["scoring_version"],
                                # Provides `row["result"]` as the `result` parameter or
                                # argument.
                                result=row["result"],
                                # Closes the multiline call or collection started on an earlier
                                # line.
                            )
                            # Closes the multiline call or collection started on an earlier line.
                        )
                    # Handles the listed exception types so the program can recover safely.
                    except (KeyError, TypeError, ValueError):
                        # Emits a runtime warning so malformed or unreadable stored data is
                        # visible.
                        warnings.warn(
                            # Adds this formatted text segment to the message being constructed.
                            f"Skipped malformed score row {reader.line_num} in {self.path}.",
                            # Includes `RuntimeWarning` in the surrounding import, call, or
                            # collection.
                            RuntimeWarning,
                            # Provides `2` as the `stacklevel` parameter or argument.
                            stacklevel=2,
                            # Closes the multiline call or collection started on an earlier line.
                        )
                        # Skips the rest of this iteration and starts the next loop iteration.
                        continue
        # Handles the listed exception types so the program can recover safely.
        except (OSError, csv.Error, UnicodeError) as exc:
            # Emits a runtime warning so malformed or unreadable stored data is visible.
            warnings.warn(
                # Adds this formatted text segment to the message being constructed.
                f"Could not read local scores from {self.path}: {exc}.",
                # Includes `RuntimeWarning` in the surrounding import, call, or collection.
                RuntimeWarning,
                # Provides `2` as the `stacklevel` parameter or argument.
                stacklevel=2,
                # Closes the multiline call or collection started on an earlier line.
            )
            # Returns `[]` to the caller as this function's result.
            return []
        # Returns `sorted(records, key=lambda item: (-item.score, item.attempts_used,
        # item.timestamp))` to the caller as this function's result.
        return sorted(records, key=lambda item: (-item.score, item.attempts_used, item.timestamp))

    # Defines the `export` function and begins its typed parameter list.
    def export(self, destination: Path | str) -> Path:
        # Computes `Path(destination)` and stores the result in `target` for later use.
        target = Path(destination)
        # Calls `target.parent.mkdir` to perform this step with the supplied arguments.
        target.parent.mkdir(parents=True, exist_ok=True)
        # Computes `self.read()` and stores the result in `records` for later use.
        records = self.read()
        # Starts a multiline function call whose arguments are supplied below.
        descriptor, temporary_name = tempfile.mkstemp(
            # Computes `target.parent, prefix=f".{target.name}.", suffix=".tmp", text=True` and
            # stores the result in `dir` for later use.
            dir=target.parent,
            # Provides the `prefix` value to the surrounding call.
            prefix=f".{target.name}.",
            # Provides the `suffix` value to the surrounding call.
            suffix=".tmp",
            # Provides the `text` value to the surrounding call.
            text=True,
            # Closes the multiline call or collection started on an earlier line.
        )
        # Starts a protected operation whose expected failures are handled below.
        try:
            # Opens a managed resource and guarantees it is closed after the nested block.
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                # Computes `csv.DictWriter(handle, fieldnames=CSV_FIELDS)` and stores the result
                # in `writer` for later use.
                writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
                # Uses the CSV writer to persist this header or record in the open file.
                writer.writeheader()
                # Iterates through `record in records` for the nested operation.
                for record in records:
                    # Uses the CSV writer to persist this header or record in the open file.
                    writer.writerow({key: csv_safe(value) for key, value in asdict(record).items()})
                # Flushes buffered file data or exposes its descriptor for durable storage.
                handle.flush()
                # Forces buffered file contents to disk before reporting the write as complete.
                os.fsync(handle.fileno())
            # Atomically replaces the destination with the completed temporary export file.
            os.replace(temporary_name, target)
        # Handles the listed exception types so the program can recover safely.
        except BaseException:
            # Calls `Path` to perform this step with the supplied arguments.
            Path(temporary_name).unlink(missing_ok=True)
            # Continues the surrounding expression or executes the next required operation.
            raise
        # Returns `target` to the caller as this function's result.
        return target
