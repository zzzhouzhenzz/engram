"""Knowledge extraction from conversation transcripts."""

import logging

import anthropic

logger = logging.getLogger(__name__)


def extract_knowledge(transcript: str, session_id: str) -> dict | None:
    """Extract structured knowledge from a conversation transcript.

    Returns a dict with keys:
        situation, tough_spot, approach, outcome, solution, keywords

    Returns None if transcript is empty or nothing worth saving.
    """
    if not transcript or not transcript.strip():
        logger.info("Empty transcript for session=%s, skipping", session_id)
        return None

    return None
