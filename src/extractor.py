"""Knowledge extraction from conversation transcripts.

STUB — will be implemented with Claude API calls later.
"""

import logging

logger = logging.getLogger(__name__)


def extract_knowledge(transcript: str, session_id: str) -> dict | None:
    """Extract structured knowledge from a conversation transcript.

    Returns a dict with keys:
        situation, tough_spot, approach, outcome, solution, keywords

    Currently a stub — returns None. Will call Claude API later.
    """
    logger.info(
        "extract_knowledge called (STUB) — session=%s, transcript_len=%d",
        session_id,
        len(transcript),
    )
    # TODO: Call Claude API to extract structured knowledge
    # - Send transcript with extraction prompt
    # - Parse structured response
    # - Return dict or None if nothing worth saving
    return None
