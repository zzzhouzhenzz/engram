# Engram Agent Guide

## Purpose

Engram is a Python/FastMCP knowledge persistence service backed by SQLite. It
originated as a Claude Code plugin; preserve that compatibility while moving
durable workflows toward Codex MCP, skills, and hooks where practical.

## Architecture

- `src/server.py`: stdio MCP tools and graceful shutdown.
- `src/db.py`: SQLite storage and indexed keyword junction table.
- `src/extractor.py`: optional API-backed knowledge extraction.
- `src/hook_session_start.py` and `src/hook_stop.py`: legacy Claude lifecycle
  integration.
- Database: `~/.engram/engram.db`.

Knowledge entries contain `situation`, `tough_spot`, `approach`, `outcome`,
`solution`, and normalized keywords.

## Compatibility and Migration

- Do not remove `.claude-plugin/`, `.mcp.json`, or Claude hooks unless explicitly
  requested; they remain legacy compatibility surfaces.
- New Codex integration should use supported MCP, skill, or hook configuration,
  with no assumption that Claude environment variables exist.
- Keep transport concerns isolated from the storage and query APIs.
- Preserve the existing database schema or provide an explicit migration.
- Never write protocol-breaking output to MCP stdout.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

All tool responses use the `[Engram]` prefix. Keywords enter the API as
comma-separated strings and are normalized to lowercase lists. Logs belong in
`~/.engram/engram.log`; stderr capture belongs in
`~/.engram/engram_stderr.log`. Investigate duplicate server instances rather
than suppressing duplicate log lines.
