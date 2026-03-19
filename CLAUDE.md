# Engram

Cross-session knowledge persistence plugin for Claude Code. Silently captures structured knowledge from conversations and resurfaces it in future sessions.

## Architecture

```
MCP Server (stdio, managed by Claude Code)
  → get_keyword_index() — list all stored keywords
  → query_knowledge(keywords) — pull relevant knowledge by keyword
  → get_recent_knowledge(n) — recent learnings
  → save_knowledge(...) — save structured knowledge (situation, tough_spot, approach, outcome, solution, keywords)
  → SQLite DB at ~/.engram/engram.db, shared across all sessions

Hooks (configured in ~/.claude/settings.json)
  → SessionStart: prints engram status, keywords, loads previous session transcript for review
  → Stop: saves session_id + transcript_path to ~/.engram/last_session.json for deferred extraction
```

## Knowledge Schema

Each entry: situation, tough_spot, approach, outcome, solution, keywords (comma-separated string → normalized list).

## Tech Stack

- Python 3.10+, FastMCP (stdio), SQLite, anthropic SDK (optional, for batch extraction)

## Components

- `src/server.py` — MCP server with 4 tools + graceful shutdown (stderr redirect, os._exit signal handlers)
- `src/db.py` — SQLite with junction table `knowledge_keywords` for indexed keyword search
- `src/extractor.py` — Knowledge extraction via Claude API (not used in main flow — Pro users lack API keys)
- `src/hook_session_start.py` — SessionStart hook: prints status, loads previous transcript for review
- `src/hook_stop.py` — Stop hook: saves session_id + transcript_path to last_session.json
- `tests/` — Unit tests for db (14), extractor (9), server (11)

## Current Setup (Manual, Working)

MCP server registered in `~/.claude.json`:
```json
"engram_mcp_server": {"type": "stdio", "command": "<venv>/bin/engram_mcp_server"}
```

Hooks registered in `~/.claude/settings.json`:
```json
"hooks": {
  "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "<venv>/bin/engram_session_start", "timeout": 5}]}],
  "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "<venv>/bin/engram_stop", "timeout": 5}]}]
}
```

## Current Task: Plugin Marketplace Packaging

**Goal**: Package engram as a Claude Code plugin installable from a self-hosted marketplace.

**Status**: IN PROGRESS — plugin.json and marketplace.json created, but remaining files not yet written.

### What's Done
- `.claude-plugin/plugin.json` — plugin manifest (metadata only)
- `.claude-plugin/marketplace.json` — self-hosted marketplace, `"source": "./"` (same repo is both marketplace and plugin)

### What's Left to Implement

1. **`.mcp.json`** — MCP server config using `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` variables
   ```json
   {"mcpServers": {"engram_mcp_server": {"command": "bash", "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/run-server.sh"]}}}
   ```

2. **`hooks/hooks.json`** — Hook config for the plugin system
   ```json
   {"hooks": {"SessionStart": [...], "Stop": [...]}}
   ```

3. **`scripts/run-server.sh`** — Bootstrap script that:
   - Creates venv in `${CLAUDE_PLUGIN_DATA}/.venv` if not exists
   - `pip install ${CLAUDE_PLUGIN_ROOT}` into it
   - `exec` the installed `engram_mcp_server`
   - This solves the chicken-and-egg: MCP server needs Python deps, but deps aren't installed until first run

4. **`scripts/run-hook.sh`** — Similar bootstrap + exec for hooks (session_start, stop)

5. **Test the full flow**: `/plugin marketplace add zzzhouzhenzz/engram` → `/plugin install engram` → verify MCP + hooks work

6. **Remove manual config** — once plugin works, the manual ~/.claude.json and ~/.claude/settings.json entries are replaced by the plugin system

### Reference: Superpowers Plugin Structure
Studied https://github.com/obra/superpowers as a reference. Key patterns:
- `marketplace.json` uses `"source": "./"` — same repo is marketplace + plugin
- `plugin.json` is just metadata — components auto-discovered from standard directories
- `hooks/hooks.json` uses `${CLAUDE_PLUGIN_ROOT}` for paths
- Cross-platform hook wrapper (`run-hook.cmd` polyglot bash/batch)

### Key Design Decisions
- **stderr redirect required**: FastMCP's transport layer logs `Starting MCP server` to stderr via rich. Claude Code treats ANY stderr as "MCP server failed"
- **os._exit(0) for signals**: `sys.exit(0)` raises SystemExit → traceback on stderr → Claude Code reports failure
- **"1 MCP server failed" on exit is a known Claude Code bug** (#18127): shutdown race condition, cosmetic only, can't fix from our side
- **No API key needed**: save_knowledge() is called by Claude directly (via MCP tool), not via Anthropic API. Pro subscription users don't have API keys
- **Deferred extraction**: Stop hook saves transcript path → next SessionStart loads and reviews → Claude calls save_knowledge() for previous session

## Known Issues

- "1 MCP server failed" on exit — Claude Code bug #18127, cosmetic. Our mitigations (stderr redirect + os._exit + show_banner=False) reduce but don't eliminate it
- Duplicate log lines appear in engram.log (two MCP server instances starting simultaneously) — investigate if two instances are spawned

## Dev Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Conventions

- All tool responses prefixed with `[Engram]`
- Keywords are comma-separated strings in the API, normalized to lowercase lists internally
- Logs go to `~/.engram/engram.log`, stderr to `~/.engram/engram_stderr.log`
- Unit tests are autonomous — write and run without asking permission
