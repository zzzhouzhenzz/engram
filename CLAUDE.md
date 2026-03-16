# Engram

Cross-session knowledge persistence for Claude Code. Automatically captures learnings from conversations and resurfaces them when relevant.

## Architecture

```
SessionStart hook
  → Load keyword index + N most recent entries
  → Inject: "Here's what you know. Use query_knowledge() when relevant."

Every ~20 turns OR session close (Stop hook)
  → Send transcript to Claude API
  → Extract structured knowledge
  → Store in SQLite

MCP Server (HTTP, localhost)
  → query_knowledge(keywords) — Claude calls on demand
  → Owns SQLite DB, shared across all sessions
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
- SQLite (local database)
- Claude API (knowledge extraction)
- MCP Server (HTTP transport, shared across sessions)
- Claude Code Hooks (SessionStart, Stop)

## Components

- `server/` — MCP HTTP server + SQLite DB
- `hooks/` — Claude Code hook scripts
- `extractor/` — Knowledge extraction via Claude API

## TODO (local only, not published)

- [ ] Vector search / semantic retrieval for keyword matching
