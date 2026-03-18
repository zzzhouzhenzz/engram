# Engram

Cross-session knowledge persistence for Claude Code. Automatically captures learnings from conversations and resurfaces them when relevant.

## Architecture

```
MCP Server (stdio, managed by Claude Code)
  → get_keyword_index() — Claude checks what knowledge exists
  → query_knowledge(keywords) — Claude pulls relevant knowledge
  → get_recent_knowledge(n) — Claude sees recent learnings
  → save_knowledge(...) — Claude saves learnings directly
  → SQLite DB shared across all sessions
```

## Knowledge Schema

Each entry is structured as:
- **Situation**: What was the context?
- **Tough spot**: What was the challenge?
- **Approach**: How did we tackle it?
- **Outcome**: What worked and what didn't?
- **Solution**: What was the final resolution?
- **Keywords**: For retrieval/matching

## Tech Stack

- Python
- SQLite (local database at ~/.engram/engram.db)
- FastMCP (stdio transport)

## Components

- `src/server.py` — MCP server with tools for querying and saving knowledge
- `src/db.py` — SQLite database layer with indexed keyword search
- `src/extractor.py` — Knowledge extraction via Claude API (available for batch use)
- `tests/` — Unit tests for all components
