"""Knowledge extraction from conversation transcripts."""

import json
import logging

import anthropic

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
Analyze this conversation transcript and extract the key learning as structured JSON.

Return a JSON object with these exact keys:
- "situation": What was the context/task?
- "tough_spot": What was the main challenge or blocker?
- "approach": How was it tackled?
- "outcome": What worked and what didn't?
- "solution": What was the final resolution?
- "keywords": List of lowercase keyword strings for retrieval

If the conversation contains no meaningful learning worth saving, return null.

Transcript:
"""

REQUIRED_FIELDS = {"situation", "tough_spot", "approach", "outcome", "solution", "keywords"}


def extract_knowledge(transcript: str, session_id: str) -> dict | None:
    """Extract structured knowledge from a conversation transcript.

    Returns a dict with keys:
        situation, tough_spot, approach, outcome, solution, keywords

    Returns None if transcript is empty or nothing worth saving.
    """
    if not transcript or not transcript.strip():
        logger.info("Empty transcript for session=%s, skipping", session_id)
        return None

    logger.info("Extracting knowledge for session=%s, transcript_len=%d", session_id, len(transcript))

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT + transcript}],
    )

    raw = response.content[0].text
    parsed = json.loads(raw)

    if parsed is None:
        return None

    if not isinstance(parsed, dict) or not REQUIRED_FIELDS.issubset(parsed.keys()):
        logger.warning("Session %s: response missing required fields", session_id)
        return None

    if not isinstance(parsed["keywords"], list):
        logger.warning("Session %s: keywords is not a list", session_id)
        return None

    return parsed
