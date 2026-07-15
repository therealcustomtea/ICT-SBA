from __future__ import annotations

from pathlib import Path

import pytest
from mastermind_cli import CSVScoreStore, ScoreRecord


def record(name: str, score: int, attempts: int = 3) -> ScoreRecord:
    return ScoreRecord(
        timestamp="2026-07-15T00:00:00+00:00",
        player_name=name,
        mode="solo",
        difficulty="normal",
        code_maker="computer",
        number_of_colours=6,
        code_length=4,
        duplicates_allowed=True,
        attempts_used=attempts,
        maximum_attempts=10,
        score=score,
        scoring_version="score_v1",
        result="won",
    )


def test_missing_file_and_header_append(tmp_path: Path) -> None:
    store = CSVScoreStore(tmp_path / "data" / "high_scores.csv")
    assert store.read() == []
    store.append(record("Ada", 1200))
    assert store.read() == [record("Ada", 1200)]
    assert (
        store.path.read_text(encoding="utf-8").splitlines()[0].startswith("timestamp,player_name")
    )


def test_scores_sort_and_skip_malformed_rows(tmp_path: Path) -> None:
    store = CSVScoreStore(tmp_path / "scores.csv")
    store.append(record("Lower", 900))
    store.append(record("Best", 1200, 4))
    store.append(record("Best fewer", 1200, 2))
    with store.path.open("a", encoding="utf-8") as handle:
        handle.write("broken,row\n")
    with pytest.warns(RuntimeWarning, match="Skipped malformed score row"):
        records = store.read()
    assert [item.player_name for item in records] == ["Best fewer", "Best", "Lower"]


def test_csv_injection_prevention_and_export(tmp_path: Path) -> None:
    store = CSVScoreStore(tmp_path / "scores.csv")
    store.append(record('=HYPERLINK("bad")', 500))
    assert "'=HYPERLINK" in store.path.read_text(encoding="utf-8")
    destination = store.export(tmp_path / "exports" / "copy.csv")
    assert destination.exists()
    assert len(destination.read_text(encoding="utf-8").splitlines()) == 2


def test_malformed_header_and_unreadable_path_warn_instead_of_crashing(tmp_path: Path) -> None:
    malformed = CSVScoreStore(tmp_path / "malformed.csv")
    malformed.path.write_text("not,the,score,header\n", encoding="utf-8")
    with pytest.warns(RuntimeWarning, match="header is malformed"):
        assert malformed.read() == []

    directory = CSVScoreStore(tmp_path)
    with pytest.warns(RuntimeWarning, match="Could not read local scores"):
        assert directory.read() == []
