"""Tests for engram.extractor — knowledge extraction via Claude API."""

import json
from unittest.mock import MagicMock, patch

import pytest

from engram.extractor import extract_knowledge

VALID_KNOWLEDGE = {
    "situation": "Setting up Python project with src layout",
    "tough_spot": "VS Code linter couldn't resolve imports",
    "approach": "Tried relative imports, then pyrightconfig.json",
    "outcome": "pyrightconfig.json worked, relative imports rejected by user",
    "solution": "Added pyrightconfig.json pointing venv at .venv",
    "keywords": ["python", "imports", "pyright", "vscode"],
}

SAMPLE_TRANSCRIPT = (
    '{"role":"user","content":"How do I fix import resolution?"}\n'
    '{"role":"assistant","content":"Try adding pyrightconfig.json"}\n'
)


def _mock_response(content: str) -> MagicMock:
    """Create a mock Anthropic API response with the given text content."""
    block = MagicMock()
    block.text = content
    response = MagicMock()
    response.content = [block]
    return response


# --- successful extraction ---


@patch("engram.extractor.anthropic")
def test_extract_returns_valid_knowledge(mock_anthropic):
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    client.messages.create.return_value = _mock_response(json.dumps(VALID_KNOWLEDGE))

    result = extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")

    assert result is not None
    assert result["situation"] == VALID_KNOWLEDGE["situation"]
    assert result["tough_spot"] == VALID_KNOWLEDGE["tough_spot"]
    assert result["keywords"] == VALID_KNOWLEDGE["keywords"]


@patch("engram.extractor.anthropic")
def test_extract_calls_api_with_transcript(mock_anthropic):
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    client.messages.create.return_value = _mock_response(json.dumps(VALID_KNOWLEDGE))

    extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")

    call_args = client.messages.create.call_args
    # Transcript should appear somewhere in the messages sent to the API
    messages = call_args.kwargs.get("messages", call_args[1].get("messages", []))
    message_text = json.dumps(messages)
    assert "import resolution" in message_text


@patch("engram.extractor.anthropic")
def test_extract_requires_all_fields(mock_anthropic):
    """Response missing required fields should return None."""
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    incomplete = {"situation": "something"}  # missing other fields
    client.messages.create.return_value = _mock_response(json.dumps(incomplete))

    result = extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")
    assert result is None


@patch("engram.extractor.anthropic")
def test_extract_keywords_must_be_list(mock_anthropic):
    """Keywords as a string instead of list should return None."""
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    bad = {**VALID_KNOWLEDGE, "keywords": "python, imports"}
    client.messages.create.return_value = _mock_response(json.dumps(bad))

    result = extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")
    assert result is None


# --- nothing worth saving ---


@patch("engram.extractor.anthropic")
def test_extract_returns_none_for_trivial(mock_anthropic):
    """API returning null/empty means nothing worth saving."""
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    client.messages.create.return_value = _mock_response("null")

    result = extract_knowledge("short chat", "session-1")
    assert result is None


@patch("engram.extractor.anthropic")
def test_extract_empty_transcript(mock_anthropic):
    result = extract_knowledge("", "session-1")
    assert result is None
    # Should not call API for empty transcript
    mock_anthropic.Anthropic.return_value.messages.create.assert_not_called()


# --- error handling ---


@patch("engram.extractor.anthropic")
def test_extract_handles_malformed_json(mock_anthropic):
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    client.messages.create.return_value = _mock_response("not valid json {{{")

    result = extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")
    assert result is None


@patch("engram.extractor.anthropic")
def test_extract_handles_api_error(mock_anthropic):
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    client.messages.create.side_effect = Exception("API rate limited")

    result = extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")
    assert result is None


# --- response with markdown fencing ---


@patch("engram.extractor.anthropic")
def test_extract_strips_markdown_code_fence(mock_anthropic):
    """API sometimes wraps JSON in ```json ... ``` blocks."""
    client = MagicMock()
    mock_anthropic.Anthropic.return_value = client
    fenced = f"```json\n{json.dumps(VALID_KNOWLEDGE)}\n```"
    client.messages.create.return_value = _mock_response(fenced)

    result = extract_knowledge(SAMPLE_TRANSCRIPT, "session-1")
    assert result is not None
    assert result["situation"] == VALID_KNOWLEDGE["situation"]
