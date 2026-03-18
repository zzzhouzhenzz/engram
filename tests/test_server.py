"""Tests for engram.server — MCP tools and hook HTTP endpoints."""

import json
from unittest.mock import patch, MagicMock

import pytest
from starlette.testclient import TestClient

from engram import db
from engram.server import mcp, query_knowledge, get_recent_knowledge, get_keyword_index


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Redirect DB to a temp directory so tests never touch real data."""
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()


@pytest.fixture()
def client():
    """Starlette test client for the MCP HTTP app."""
    app = mcp.http_app()
    return TestClient(app)


# --- Health endpoint ---


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# --- SessionStart hook ---


def test_session_start_empty_db(client):
    resp = client.post("/hooks/session-start")
    body = resp.json()
    assert resp.status_code == 200
    assert body["continue"] is True
    assert body["hookSpecificOutput"]["additionalContext"] == ""


def test_session_start_with_knowledge(client):
    db.insert_knowledge("s1", "deploying app", "OOM crash", "added memory",
                        "worked", "increase limits", ["docker", "oom"])
    resp = client.post("/hooks/session-start")
    body = resp.json()
    context = body["hookSpecificOutput"]["additionalContext"]
    assert "docker" in context
    assert "oom" in context
    assert "deploying app" in context


def test_session_start_returns_keywords_and_recent(client):
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["python"])
    db.insert_knowledge("s2", "sit2", "", "", "", "", ["rust"])
    resp = client.post("/hooks/session-start")
    context = resp.json()["hookSpecificOutput"]["additionalContext"]
    assert "python" in context
    assert "rust" in context
    assert "query_knowledge" in context


# --- Stop hook ---


def test_stop_increments_turn(client):
    resp = client.post("/hooks/stop", json={"session_id": "s1", "transcript_path": ""})
    assert resp.status_code == 200
    assert resp.json()["turn_count"] == 1

    resp = client.post("/hooks/stop", json={"session_id": "s1", "transcript_path": ""})
    assert resp.json()["turn_count"] == 2


def test_stop_no_extraction_before_interval(client):
    """Extraction should not trigger before EXTRACTION_INTERVAL turns."""
    with patch("engram.server.extract_knowledge") as mock_extract:
        for _ in range(5):
            client.post("/hooks/stop", json={"session_id": "s1", "transcript_path": "/tmp/fake"})
        mock_extract.assert_not_called()


def test_stop_triggers_extraction_at_interval(client, tmp_path):
    """Extraction should trigger at EXTRACTION_INTERVAL turns."""
    transcript_file = tmp_path / "transcript.jsonl"
    transcript_file.write_text('{"role":"user","content":"hello"}')

    with patch("engram.server.EXTRACTION_INTERVAL", 3), \
         patch("engram.server.extract_knowledge") as mock_extract:
        mock_extract.return_value = {
            "situation": "test situation",
            "tough_spot": "test tough spot",
            "approach": "test approach",
            "outcome": "test outcome",
            "solution": "test solution",
            "keywords": ["test"],
        }
        for _ in range(3):
            client.post("/hooks/stop", json={
                "session_id": "s1",
                "transcript_path": str(transcript_file),
            })

        mock_extract.assert_called_once()

    # Knowledge should be stored
    results = db.search_by_keywords(["test"])
    assert len(results) == 1
    assert results[0]["situation"] == "test situation"


def test_stop_resets_counter_after_extraction(client, tmp_path):
    transcript_file = tmp_path / "transcript.jsonl"
    transcript_file.write_text('{"role":"user","content":"hello"}')

    with patch("engram.server.EXTRACTION_INTERVAL", 2), \
         patch("engram.server.extract_knowledge", return_value=None):
        client.post("/hooks/stop", json={"session_id": "s1", "transcript_path": str(transcript_file)})
        client.post("/hooks/stop", json={"session_id": "s1", "transcript_path": str(transcript_file)})

    # Counter should be reset after extraction attempt
    assert db.get_turn_count("s1") == 0


def test_stop_handles_missing_body(client):
    resp = client.post("/hooks/stop")
    assert resp.status_code == 200
    assert resp.json()["turn_count"] == 1


def test_stop_no_extraction_without_transcript_path(client):
    """Even at interval, don't extract if no transcript_path."""
    with patch("engram.server.EXTRACTION_INTERVAL", 1), \
         patch("engram.server.extract_knowledge") as mock_extract:
        client.post("/hooks/stop", json={"session_id": "s1", "transcript_path": ""})
        mock_extract.assert_not_called()


# --- MCP tools (called as plain functions) ---


def test_query_knowledge_no_keywords():
    assert query_knowledge("") == "No keywords provided."
    assert query_knowledge("  , , ") == "No keywords provided."


def test_query_knowledge_with_results():
    db.insert_knowledge("s1", "sit1", "tough1", "approach1", "outcome1",
                        "solution1", ["python", "imports"])
    result = query_knowledge("python")
    assert "sit1" in result
    assert "tough1" in result


def test_query_knowledge_no_results():
    result = query_knowledge("nonexistent")
    assert "No knowledge found" in result


def test_get_recent_knowledge_empty():
    assert get_recent_knowledge() == "No knowledge entries yet."


def test_get_recent_knowledge_with_data():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["kw"])
    result = get_recent_knowledge(5)
    assert "sit1" in result


def test_get_keyword_index_empty():
    assert get_keyword_index() == "No keywords yet."


def test_get_keyword_index_with_data():
    db.insert_knowledge("s1", "sit1", "", "", "", "", ["alpha", "beta"])
    result = get_keyword_index()
    assert "alpha" in result
    assert "beta" in result
