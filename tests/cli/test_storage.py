# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `pathlib` for use in this module.
from pathlib import Path

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_cli` for use in this module.
from mastermind_cli import CSVScoreStore, ScoreRecord


# Defines the `record` callable and its typed interface.
def record(name: str, score: int, attempts: int = 3) -> ScoreRecord:
    # Returns this result to the caller and ends the current function.
    return ScoreRecord(
        # Provides the `timestamp` parameter or keyword argument.
        timestamp="2026-07-15T00:00:00+00:00",
        # Provides the `player_name` parameter or keyword argument.
        player_name=name,
        # Provides the `mode` parameter or keyword argument.
        mode="solo",
        # Provides the `difficulty` parameter or keyword argument.
        difficulty="normal",
        # Provides the `code_maker` parameter or keyword argument.
        code_maker="computer",
        # Provides the `number_of_colours` parameter or keyword argument.
        number_of_colours=6,
        # Provides the `code_length` parameter or keyword argument.
        code_length=4,
        # Provides the `duplicates_allowed` parameter or keyword argument.
        duplicates_allowed=True,
        # Provides the `attempts_used` parameter or keyword argument.
        attempts_used=attempts,
        # Provides the `maximum_attempts` parameter or keyword argument.
        maximum_attempts=10,
        # Provides the `score` parameter or keyword argument.
        score=score,
        # Provides the `scoring_version` parameter or keyword argument.
        scoring_version="score_v1",
        # Provides the `result` parameter or keyword argument.
        result="won",
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `test_missing_file_and_header_append` callable and its typed interface.
def test_missing_file_and_header_append(tmp_path: Path) -> None:
    # Computes and stores `store` for subsequent operations.
    store = CSVScoreStore(tmp_path / "data" / "high_scores.csv")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert store.read() == []
    # Calls `store.append` with the supplied values.
    store.append(record("Ada", 1200))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert store.read() == [record("Ada", 1200)]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (
        # Calls `store.path.read_text` with the supplied values.
        store.path.read_text(encoding="utf-8").splitlines()[0].startswith("timestamp,player_name")
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `test_scores_sort_and_skip_malformed_rows` callable and its typed interface.
def test_scores_sort_and_skip_malformed_rows(tmp_path: Path) -> None:
    # Computes and stores `store` for subsequent operations.
    store = CSVScoreStore(tmp_path / "scores.csv")
    # Calls `store.append` with the supplied values.
    store.append(record("Lower", 900))
    # Calls `store.append` with the supplied values.
    store.append(record("Best", 1200, 4))
    # Calls `store.append` with the supplied values.
    store.append(record("Best fewer", 1200, 2))
    # Acquires this managed resource and guarantees cleanup afterward.
    with store.path.open("a", encoding="utf-8") as handle:
        # Calls `handle.write` with the supplied values.
        handle.write("broken,row\n")
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.warns(RuntimeWarning, match="Skipped malformed score row"):
        # Computes and stores `records` for subsequent operations.
        records = store.read()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert [item.player_name for item in records] == ["Best fewer", "Best", "Lower"]


# Defines the `test_csv_injection_prevention_and_export` callable and its typed interface.
def test_csv_injection_prevention_and_export(tmp_path: Path) -> None:
    # Computes and stores `store` for subsequent operations.
    store = CSVScoreStore(tmp_path / "scores.csv")
    # Calls `store.append` with the supplied values.
    store.append(record('=HYPERLINK("bad")', 500))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "'=HYPERLINK" in store.path.read_text(encoding="utf-8")
    # Computes and stores `destination` for subsequent operations.
    destination = store.export(tmp_path / "exports" / "copy.csv")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert destination.exists()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(destination.read_text(encoding="utf-8").splitlines()) == 2


# Defines the `test_malformed_header_and_unreadable_path_warn_instead_of_crashing` callable and its
# typed interface.
def test_malformed_header_and_unreadable_path_warn_instead_of_crashing(tmp_path: Path) -> None:
    # Computes and stores `malformed` for subsequent operations.
    malformed = CSVScoreStore(tmp_path / "malformed.csv")
    # Calls `malformed.path.write_text` with the supplied values.
    malformed.path.write_text("not,the,score,header\n", encoding="utf-8")
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.warns(RuntimeWarning, match="header is malformed"):
        # Asserts this invariant so an unexpected test state fails immediately.
        assert malformed.read() == []

    # Computes and stores `directory` for subsequent operations.
    directory = CSVScoreStore(tmp_path)
    # Acquires this managed resource and guarantees cleanup afterward.
    with pytest.warns(RuntimeWarning, match="Could not read local scores"):
        # Asserts this invariant so an unexpected test state fails immediately.
        assert directory.read() == []
