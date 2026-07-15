from __future__ import annotations

import csv
import os
import tempfile
import warnings
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

CSV_FIELDS = (
    "timestamp",
    "player_name",
    "mode",
    "difficulty",
    "code_maker",
    "number_of_colours",
    "code_length",
    "duplicates_allowed",
    "attempts_used",
    "maximum_attempts",
    "score",
    "scoring_version",
    "result",
)


def csv_safe(value: object) -> str:
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


@dataclass(frozen=True, slots=True)
class ScoreRecord:
    timestamp: str
    player_name: str
    mode: str
    difficulty: str
    code_maker: str
    number_of_colours: int
    code_length: int
    duplicates_allowed: bool
    attempts_used: int
    maximum_attempts: int
    score: int
    scoring_version: str
    result: str

    @classmethod
    def now(cls, **values: object) -> ScoreRecord:
        return cls(timestamp=datetime.now(UTC).isoformat(), **values)  # type: ignore[arg-type]


class CSVScoreStore:
    def __init__(self, path: Path | str = Path("data/high_scores.csv")) -> None:
        self.path = Path(path)

    def append(self, record: ScoreRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if needs_header:
                writer.writeheader()
            writer.writerow({key: csv_safe(value) for key, value in asdict(record).items()})
            handle.flush()
            os.fsync(handle.fileno())

    def read(self) -> list[ScoreRecord]:
        if not self.path.exists():
            return []
        records: list[ScoreRecord] = []
        try:
            with self.path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames or not set(CSV_FIELDS).issubset(reader.fieldnames):
                    warnings.warn(
                        f"Ignored {self.path}: the score file header is malformed.",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                    return []
                for row in reader:
                    try:
                        records.append(
                            ScoreRecord(
                                timestamp=row["timestamp"],
                                player_name=row["player_name"],
                                mode=row["mode"],
                                difficulty=row["difficulty"],
                                code_maker=row["code_maker"],
                                number_of_colours=int(row["number_of_colours"]),
                                code_length=int(row["code_length"]),
                                duplicates_allowed=row["duplicates_allowed"].casefold() == "true",
                                attempts_used=int(row["attempts_used"]),
                                maximum_attempts=int(row["maximum_attempts"]),
                                score=int(row["score"]),
                                scoring_version=row["scoring_version"],
                                result=row["result"],
                            )
                        )
                    except (KeyError, TypeError, ValueError):
                        warnings.warn(
                            f"Skipped malformed score row {reader.line_num} in {self.path}.",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                        continue
        except (OSError, csv.Error, UnicodeError) as exc:
            warnings.warn(
                f"Could not read local scores from {self.path}: {exc}.",
                RuntimeWarning,
                stacklevel=2,
            )
            return []
        return sorted(records, key=lambda item: (-item.score, item.attempts_used, item.timestamp))

    def export(self, destination: Path | str) -> Path:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        records = self.read()
        descriptor, temporary_name = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", text=True
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
                writer.writeheader()
                for record in records:
                    writer.writerow({key: csv_safe(value) for key, value in asdict(record).items()})
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        except BaseException:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        return target
