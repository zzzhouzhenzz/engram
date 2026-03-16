"""Engram MCP server — knowledge persistence for Claude Code.

Exposes MCP tools for querying knowledge + HTTP hook endpoints
for SessionStart and Stop lifecycle events.
"""

import logging
import threading
import time
from pathlib import Path

import uvicorn
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from engram import db
from engram.extractor import extract_knowledge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("engram")

EXTRACTION_INTERVAL = 20  # Extract knowledge every N turns
IDLE_TIMEOUT_SECONDS = 30 * 60  # 30 minutes

# --- Idle timeout tracker ---

_last_activity = time.monotonic()
_shutdown_event = threading.Event()


def _touch_activity():
    """Reset idle timer on any activity."""
    global _last_activity
    _last_activity = time.monotonic()


def _idle_watchdog(server: uvicorn.Server):
    """Background thread that shuts down the server after idle timeout."""
    while not _shutdown_event.is_set():
        elapsed = time.monotonic() - _last_activity
        remaining = IDLE_TIMEOUT_SECONDS - elapsed
        if remaining <= 0:
            logger.info("Idle timeout reached (%ds). Shutting down.", IDLE_TIMEOUT_SECONDS)
            server.should_exit = True
            return
        _shutdown_event.wait(timeout=min(remaining, 60))


# --- MCP Server ---

mcp = FastMCP("engram_mcp_server")


@mcp.tool()
def query_knowledge(keywords: str) -> str:
    """Search the knowledge base by keywords.

    Args:
        keywords: Comma-separated keywords to search for.

    Returns:
        Matching knowledge entries as formatted text.
    """
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        return "No keywords provided."

    results = db.search_by_keywords(kw_list)
    if not results:
        return f"No knowledge found for keywords: {keywords}"

    return _format_entries(results)


@mcp.tool()
def get_recent_knowledge(n: int = 5) -> str:
    """Get the N most recent knowledge entries.

    Args:
        n: Number of recent entries to return (default 5).

    Returns:
        Recent knowledge entries as formatted text.
    """
    results = db.get_recent(n)
    if not results:
        return "No knowledge entries yet."

    return _format_entries(results)


@mcp.tool()
def get_keyword_index() -> str:
    """Get all keywords stored in the knowledge base.

    Returns:
        Comma-separated list of all keywords.
    """
    keywords = db.get_all_keywords()
    if not keywords:
        return "No keywords yet."
    return ", ".join(keywords)


# --- Hook HTTP Endpoints ---


@mcp.custom_route("/hooks/session-start", methods=["POST"])
async def hook_session_start(request: Request):
    """Called by SessionStart hook. Returns context to inject."""
    _touch_activity()
    keywords = db.get_all_keywords()
    recent = db.get_recent(3)

    parts = []

    if keywords:
        parts.append(
            "[Engram Knowledge Base]\n"
            f"Available knowledge keywords: {', '.join(keywords)}\n"
            "Use the query_knowledge tool when you encounter situations "
            "related to these keywords."
        )

    if recent:
        parts.append("[Recent Learnings]\n" + _format_entries(recent))

    if not parts:
        return PlainTextResponse("No knowledge stored yet.")

    return PlainTextResponse("\n\n".join(parts))


@mcp.custom_route("/hooks/stop", methods=["POST"])
async def hook_stop(request: Request):
    """Called by Stop hook. Tracks turns, triggers extraction."""
    _touch_activity()
    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = body.get("session_id", "unknown")
    transcript_path = body.get("transcript_path", "")

    # Increment turn counter
    turn_count = db.increment_turn(session_id)
    logger.info("Session %s: turn %d", session_id, turn_count)

    # Check if we should extract
    should_extract = turn_count >= EXTRACTION_INTERVAL

    if should_extract and transcript_path:
        logger.info(
            "Session %s: triggering extraction at turn %d",
            session_id,
            turn_count,
        )
        transcript = _read_transcript(transcript_path)
        if transcript:
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
            # Reset counter after extraction attempt
            db.reset_turn_count(session_id)

    return JSONResponse({"status": "ok", "turn_count": turn_count})


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request):
    _touch_activity()
    return JSONResponse({"status": "healthy", "service": "engram"})


# --- Helpers ---


def _format_entries(entries: list[dict]) -> str:
    parts = []
    for e in entries:
        keywords = e.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        parts.append(
            f"---\n"
            f"**Situation**: {e.get('situation', 'N/A')}\n"
            f"**Tough spot**: {e.get('tough_spot', 'N/A')}\n"
            f"**Approach**: {e.get('approach', 'N/A')}\n"
            f"**Outcome**: {e.get('outcome', 'N/A')}\n"
            f"**Solution**: {e.get('solution', 'N/A')}\n"
            f"**Keywords**: {', '.join(keywords)}\n"
        )
    return "\n".join(parts)


def _read_transcript(path: str) -> str | None:
    """Read a JSONL transcript file and return as string."""
    p = Path(path)
    if not p.exists():
        logger.warning("Transcript not found: %s", path)
        return None
    try:
        return p.read_text()
    except Exception as e:
        logger.error("Failed to read transcript: %s", e)
        return None


# --- Entry point ---


def main():
    logger.info("Initializing engram database...")
    db.init_db()

    logger.info("Starting engram MCP server on http://localhost:7777")

    app = mcp.http_app()

    config = uvicorn.Config(app, host="127.0.0.1", port=7777, log_level="info")
    server = uvicorn.Server(config)

    # Start idle watchdog
    watchdog = threading.Thread(target=_idle_watchdog, args=(server,), daemon=True)
    watchdog.start()

    server.run()


if __name__ == "__main__":
    main()
