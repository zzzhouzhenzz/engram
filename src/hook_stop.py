"""Stop hook — saves session info for extraction on next session start."""

import json
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".engram"
LAST_SESSION_PATH = STATE_DIR / "last_session.json"


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    session_id = payload.get("session_id", "")
    transcript_path = payload.get("transcript_path", "")

    if not session_id or not transcript_path:
        return

    LAST_SESSION_PATH.write_text(json.dumps({
        "session_id": session_id,
        "transcript_path": transcript_path,
    }))


if __name__ == "__main__":
    main()
