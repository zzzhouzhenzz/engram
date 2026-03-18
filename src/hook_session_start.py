"""SessionStart hook — prints engram context and previous session for review."""

import json
from pathlib import Path

from engram import db

STATE_DIR = Path.home() / ".engram"
LAST_SESSION_PATH = STATE_DIR / "last_session.json"
MAX_TRANSCRIPT_CHARS = 50000  # Limit transcript size to avoid overwhelming context


def _load_previous_session() -> str | None:
    """Load and consume the previous session transcript, if any."""
    if not LAST_SESSION_PATH.exists():
        return None

    try:
        data = json.loads(LAST_SESSION_PATH.read_text())
        LAST_SESSION_PATH.unlink()  # Consume it — don't process twice
    except Exception:
        return None

    transcript_path = data.get("transcript_path", "")
    if not transcript_path:
        return None

    p = Path(transcript_path)
    if not p.exists():
        return None

    try:
        transcript = p.read_text()
    except Exception:
        return None

    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        transcript = transcript[-MAX_TRANSCRIPT_CHARS:]

    return transcript


def main():
    db.init_db()
    keywords = db.get_all_keywords()
    recent = db.get_recent(3)

    print("[Engram] Cross-session knowledge persistence is active.")

    if keywords:
        print(f"Available keywords: {', '.join(keywords)}")
        print("Use query_knowledge() when you encounter a relevant situation.")
    else:
        print("No knowledge stored yet.")

    if recent:
        print("\nRecent learnings:")
        for e in recent:
            kws = e.get("keywords", [])
            if isinstance(kws, str):
                kws = [kws]
            print(f"  - {e.get('situation', 'N/A')} [{', '.join(kws)}]")

    # Check for unprocessed previous session
    prev_transcript = _load_previous_session()
    if prev_transcript:
        print("\n[Engram] PREVIOUS SESSION TRANSCRIPT FOR REVIEW:")
        print("Review the following transcript from a previous session.")
        print("If anything non-trivial was learned or solved, call save_knowledge().")
        print("If it was just a trivial conversation, skip saving.")
        print("---BEGIN TRANSCRIPT---")
        print(prev_transcript)
        print("---END TRANSCRIPT---")
    else:
        print("\nUse save_knowledge() when you solve non-trivial problems.")


if __name__ == "__main__":
    main()
