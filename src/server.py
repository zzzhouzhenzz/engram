"""Engram MCP server — knowledge persistence for Claude Code.

Exposes MCP tools for querying and saving knowledge.
Runs via stdio transport — Claude Code manages the lifecycle.
"""

import logging

from fastmcp import FastMCP

from engram import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("engram")

# --- MCP Server ---

mcp = FastMCP("engram_mcp_server")


@mcp.tool()
def query_knowledge(keywords: str) -> str:
    """Search the knowledge base by keywords.

    Call this when you encounter a situation that might match stored knowledge.
    Use get_keyword_index() first to see available keywords.

    Args:
        keywords: Comma-separated keywords to search for.

    Returns:
        Matching knowledge entries as formatted text.
    """
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        return "[Engram] No keywords provided."

    results = db.search_by_keywords(kw_list)
    if not results:
        return f"[Engram] No knowledge found for keywords: {keywords}"

    return "[Engram] Found knowledge:\n\n" + _format_entries(results)


@mcp.tool()
def get_recent_knowledge(n: int = 5) -> str:
    """Get the N most recent knowledge entries.

    Call this at the start of a session to see what was learned recently.

    Args:
        n: Number of recent entries to return (default 5).

    Returns:
        Recent knowledge entries as formatted text.
    """
    results = db.get_recent(n)
    if not results:
        return "[Engram] No knowledge entries yet."

    return "[Engram] Recent knowledge:\n\n" + _format_entries(results)


@mcp.tool()
def get_keyword_index() -> str:
    """Get all keywords stored in the knowledge base.

    Call this at the start of a session to know what knowledge is available.
    Then use query_knowledge() when you encounter a relevant situation.

    Returns:
        Comma-separated list of all keywords.
    """
    keywords = db.get_all_keywords()
    if not keywords:
        return "[Engram] No keywords yet."
    return "[Engram] Available keywords: " + ", ".join(keywords)


@mcp.tool()
def save_knowledge(
    situation: str,
    tough_spot: str,
    approach: str,
    outcome: str,
    solution: str,
    keywords: str,
) -> str:
    """Save a learning from the current session to the knowledge base.

    Call this when you and the user have solved a non-trivial problem,
    debugged a tricky issue, or discovered something worth remembering
    for future sessions. Do NOT save trivial or obvious things.

    Args:
        situation: What was the context/task?
        tough_spot: What was the main challenge or blocker?
        approach: How was it tackled?
        outcome: What worked and what didn't?
        solution: What was the final resolution?
        keywords: Comma-separated lowercase keywords for retrieval.

    Returns:
        Confirmation message.
    """
    kw_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        return "[Engram] Error: at least one keyword is required."

    kid = db.insert_knowledge(
        session_id="",
        situation=situation,
        tough_spot=tough_spot,
        approach=approach,
        outcome=outcome,
        solution=solution,
        keywords=kw_list,
    )
    logger.info("Knowledge saved (id=%s, keywords=%s)", kid, kw_list)
    return f"[Engram] Knowledge saved with keywords: {', '.join(kw_list)}"


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


# --- Entry point ---


def main():
    logger.info("Initializing engram database...")
    db.init_db()

    logger.info("Starting engram MCP server (stdio)")
    mcp.run()


if __name__ == "__main__":
    main()
