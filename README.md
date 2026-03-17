# Engram

> Silent knowledge persistence for Claude Code — your AI pair programmer remembers what you've learned.

Engram automatically captures problem-solving knowledge from your Claude Code sessions and resurfaces it when you encounter similar situations. No manual note-taking, no copy-pasting into files — it just works.

## The Problem

You solve a tricky problem with Claude Code. A week later, you hit the same situation. But the session is gone, your memory is fuzzy, and you start from scratch.

## How It Works

1. **Auto-capture**: After every ~20 interactions (or when you close a session), Engram extracts structured knowledge — what the problem was, what you tried, what worked, and the final solution.
2. **Auto-surface**: When you start a new session, Engram loads a keyword index. As you work, Claude recognizes relevant knowledge and pulls it in on demand.
3. **Cross-session**: A shared local database means knowledge from any session is instantly available to all others.

## Knowledge Format

Each captured entry contains:

| Field | Description |
|-------|-------------|
| Situation | What was the context? |
| Tough spot | What was the challenge? |
| Approach | How did we tackle it? |
| Outcome | What worked and what didn't? |
| Solution | Final resolution |
| Keywords | For retrieval and matching |

## Setup

```bash
# 1. Clone and install
git clone https://github.com/zzzhouzhenzz/engram.git
cd engram
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 2. Add hooks to ~/.claude/settings.json
# Merge the "hooks" block from hooks.json into your settings.
# Use "_hooks_disabled" as the key to install without enabling.
# Rename to "hooks" when ready to activate.

# 3. Register MCP server (run once)
claude mcp add --transport http --scope user engram_mcp_server http://localhost:7777/mcp
```

The server auto-starts on your first Claude Code session and auto-stops after 30 minutes of inactivity.

## License

MIT
