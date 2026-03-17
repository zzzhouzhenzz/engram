"""Tests for engram.db — SQLite knowledge store."""

import pytest

from engram import db


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Redirect DB to a temp directory so tests never touch real data."""
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


# --- insert + retrieve ---


def test_insert_and_get_recent():
    kid = db.insert_knowledge(
        session_id="s1",
        situation="deploying to prod",
        tough_spot="container kept OOMing",
        approach="increased memory limit",
        outcome="worked but slow",
        solution="switched to streaming",
        keywords=["docker", "OOM", "streaming"],
    )
    assert kid is not None

    recent = db.get_recent(5)
    assert len(recent) == 1
    assert recent[0]["situation"] == "deploying to prod"
    assert recent[0]["keywords"] == ["docker", "oom", "streaming"]


def test_get_recent_respects_limit():
    for i in range(5):
        db.insert_knowledge(f"s{i}", f"sit{i}", "", "", "", "", [f"kw{i}"])

    assert len(db.get_recent(3)) == 3
    assert len(db.get_recent(10)) == 5


# --- keyword search ---


def test_search_by_keywords_exact_match():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["python", "sqlite"])
    db.insert_knowledge("s2", "sit2", "", "", "", "", ["rust", "sqlite"])

    results = db.search_by_keywords(["python"])
    assert len(results) == 1
    assert results[0]["situation"] == "sit1"


def test_search_by_keywords_multiple():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["python"])
    db.insert_knowledge("s2", "sit2", "", "", "", "", ["rust"])
    db.insert_knowledge("s3", "sit3", "", "", "", "", ["go"])

    results = db.search_by_keywords(["python", "rust"])
    assert len(results) == 2


def test_search_by_keywords_no_duplicates():
    """Entry with multiple matching keywords should appear once."""
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["python", "sqlite"])

    results = db.search_by_keywords(["python", "sqlite"])
    assert len(results) == 1


def test_search_by_keywords_case_insensitive():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["Python"])

    results = db.search_by_keywords(["python"])
    assert len(results) == 1

    results = db.search_by_keywords(["PYTHON"])
    assert len(results) == 1


def test_search_by_keywords_empty():
    assert db.search_by_keywords([]) == []
    assert db.search_by_keywords(["  ", ""]) == []


def test_search_by_keywords_no_match():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["python"])

    results = db.search_by_keywords(["javascript"])
    assert len(results) == 0


# --- keyword index ---


def test_get_all_keywords():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["python", "sqlite"])
    db.insert_knowledge("s2", "sit2", "", "", "", "", ["rust", "sqlite"])

    keywords = db.get_all_keywords()
    assert keywords == ["python", "rust", "sqlite"]


def test_get_all_keywords_empty():
    assert db.get_all_keywords() == []


# --- session turn tracking ---


def test_increment_turn_new_session():
    assert db.increment_turn("s1") == 1
    assert db.increment_turn("s1") == 2
    assert db.increment_turn("s1") == 3


def test_increment_turn_independent_sessions():
    db.increment_turn("s1")
    db.increment_turn("s1")
    db.increment_turn("s2")

    assert db.get_turn_count("s1") == 2
    assert db.get_turn_count("s2") == 1


def test_get_turn_count_unknown_session():
    assert db.get_turn_count("nonexistent") == 0


def test_reset_turn_count():
    db.increment_turn("s1")
    db.increment_turn("s1")
    db.increment_turn("s1")
    assert db.get_turn_count("s1") == 3

    db.reset_turn_count("s1")
    assert db.get_turn_count("s1") == 0
