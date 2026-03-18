"""Stop hook — tracks turns and triggers knowledge extraction."""

import json
import logging
import sys
from pathlib import Path

from engram import db
from engram.extractor import extract_knowledge

LOG_DIR = Path.home() / ".engram"
LOG_PATH = LOG_DIR / "engram.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler(LOG_PATH)],
)
logger = logging.getLogger("engram.hook_stop")

EXTRACTION_INTERVAL = 20


def main():
    db.init_db()

    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    session_id = payload.get("session_id", "unknown")
    transcript_path = payload.get("transcript_path", "")

    turn_count = db.increment_turn(session_id)
    logger.info("Session %s: turn %d", session_id, turn_count)

    if turn_count < EXTRACTION_INTERVAL:
        return

    if not transcript_path:
        logger.warning("Session %s: no transcript_path at turn %d", session_id, turn_count)
        return

    p = Path(transcript_path)
    if not p.exists():
        logger.warning("Session %s: transcript not found: %s", session_id, transcript_path)
        return

    try:
        transcript = p.read_text()
    except Exception as e:
        logger.error("Session %s: failed to read transcript: %s", session_id, e)
        return

    logger.info("Session %s: extracting knowledge at turn %d", session_id, turn_count)
    result = extract_knowledge(transcript, session_id)

    if result:
        db.insert_knowledge(
            session_id=session_id,
            situation=result.get("situation", ""),
            tough_spot=result.get("tough_spot", ""),
            approach=result.get("approach", ""),
            outcome=result.get("outcome", ""),
            solution=result.get("solution", ""),
            keywords=result.get("keywords", []),
        )
        logger.info("Session %s: knowledge saved", session_id)

    db.reset_turn_count(session_id)


if __name__ == "__main__":
    main()
