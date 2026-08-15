"""Unit tests for the ScoreStore SQLite persistence layer."""

import pytest

from src.core.score_store import ScoreStore


def _make_store(tmp_path):
    return ScoreStore(db_path=str(tmp_path / "scores.db"))


def test_first_game_inserts_record(tmp_path):
    store = _make_store(tmp_path)
    store.upsert_best("Ana", 12, 3)
    assert store.top_scores() == [(1, "Ana", 12, 3)]


def test_update_only_when_surpasses(tmp_path):
    store = _make_store(tmp_path)
    store.upsert_best("Ana", 12, 3)
    store.upsert_best("Ana", 20, 4)
    assert store.top_scores() == [(1, "Ana", 20, 4)]


def test_keeps_record_when_not_surpassed(tmp_path):
    store = _make_store(tmp_path)
    store.upsert_best("Ana", 20, 4)
    store.upsert_best("Ana", 12, 3)
    assert store.top_scores() == [(1, "Ana", 20, 4)]


def test_keeps_record_when_equal(tmp_path):
    store = _make_store(tmp_path)
    store.upsert_best("Ana", 20, 4)
    store.upsert_best("Ana", 20, 5)
    assert store.top_scores() == [(1, "Ana", 20, 4)]


def test_top_scores_orders_by_coins_desc(tmp_path):
    store = _make_store(tmp_path)
    store.upsert_best("Ana", 10, 2)
    store.upsert_best("Bea", 30, 5)
    store.upsert_best("Caro", 20, 3)
    assert store.top_scores() == [
        (1, "Bea", 30, 5),
        (2, "Caro", 20, 3),
        (3, "Ana", 10, 2),
    ]


def test_top_scores_limited_to_five(tmp_path):
    store = _make_store(tmp_path)
    for i in range(1, 8):
        store.upsert_best(f"Player{i}", i * 10, 1)
    rows = store.top_scores(5)
    assert len(rows) == 5
    assert rows[0][1] == "Player7"
    assert rows[-1][1] == "Player3"


def test_persists_across_reopen(tmp_path):
    db = str(tmp_path / "scores.db")
    store = ScoreStore(db_path=db)
    store.upsert_best("Ana", 15, 4)
    store.close()

    reopened = ScoreStore(db_path=db)
    assert reopened.top_scores() == [(1, "Ana", 15, 4)]
    reopened.close()


def test_empty_name_is_ignored(tmp_path):
    store = _make_store(tmp_path)
    store.upsert_best("   ", 5, 1)
    assert store.top_scores() == []


def test_module_imports_without_camera_or_models(tmp_path):
    """ScoreStore can be instantiated without any camera or model files."""
    store = _make_store(tmp_path)
    assert store is not None
    store.close()