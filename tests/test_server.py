"""Tests for engram.server — MCP tools."""

import pytest

from engram import db
from engram.server import query_knowledge, get_recent_knowledge, get_keyword_index, save_knowledge


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Redirect DB to a temp directory so tests never touch real data."""
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


# --- query_knowledge ---


def test_query_knowledge_no_keywords():
    assert query_knowledge("") == "[Engram] No keywords provided."
    assert query_knowledge("  , , ") == "[Engram] No keywords provided."


def test_query_knowledge_with_results():
    db.insert_knowledge("s1", "sit1", "tough1", "approach1", "outcome1",
                        "solution1", ["python", "imports"])
    result = query_knowledge("python")
    assert "sit1" in result
    assert "tough1" in result


def test_query_knowledge_no_results():
    result = query_knowledge("nonexistent")
    assert "No knowledge found" in result


# --- get_recent_knowledge ---


def test_get_recent_knowledge_empty():
    assert get_recent_knowledge() == "[Engram] No knowledge entries yet."


def test_get_recent_knowledge_with_data():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["kw"])
    result = get_recent_knowledge(5)
    assert "sit1" in result


# --- get_keyword_index ---


def test_get_keyword_index_empty():
    assert get_keyword_index() == "[Engram] No keywords yet."


def test_get_keyword_index_with_data():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["alpha", "beta"])
    result = get_keyword_index()
    assert "alpha" in result
    assert "beta" in result


# --- save_knowledge ---


def test_save_knowledge():
    result = save_knowledge(
        situation="setting up Python imports",
        tough_spot="VS Code linter couldn't resolve",
        approach="tried relative imports, then pyrightconfig",
        outcome="pyrightconfig worked",
        solution="added pyrightconfig.json pointing to .venv",
        keywords="python, imports, pyright",
    )
    assert "Knowledge saved" in result
    assert "python" in result

    # Verify it's in the DB
    results = db.search_by_keywords(["python"])
    assert len(results) == 1
    assert results[0]["situation"] == "setting up Python imports"


def test_save_knowledge_normalizes_keywords():
    save_knowledge("sit", "tough", "approach", "outcome", "solution", "Python, IMPORTS")
    results = db.search_by_keywords(["python"])
    assert len(results) == 1
    assert results[0]["keywords"] == ["python", "imports"]


def test_save_knowledge_requires_keywords():
    result = save_knowledge("sit", "tough", "approach", "outcome", "solution", "")
    assert "Error" in result


def test_save_knowledge_searchable():
    save_knowledge("sit1", "tough1", "app1", "out1", "sol1", "docker, oom")
    save_knowledge("sit2", "tough2", "app2", "out2", "sol2", "python, imports")

    docker_results = db.search_by_keywords(["docker"])
    assert len(docker_results) == 1
    assert docker_results[0]["situation"] == "sit1"

    python_results = db.search_by_keywords(["python"])
    assert len(python_results) == 1
    assert python_results[0]["situation"] == "sit2"
