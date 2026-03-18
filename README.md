# Engram

> Silent knowledge persistence for Claude Code — your AI pair programmer remembers what you've learned.

Engram automatically captures problem-solving knowledge from your Claude Code sessions and resurfaces it when you encounter similar situations. No manual note-taking, no copy-pasting into files — it just works.

## The Problem

You solve a tricky problem with Claude Code. A week later, you hit the same situation. But the session is gone, your memory is fuzzy, and you start from scratch.

## How It Works

1. **Auto-surface**: When Claude sees the engram tools, it checks the keyword index and pulls in relevant knowledge on demand.
2. **Auto-save**: When you solve a non-trivial problem, Claude saves the learning — what the problem was, what you tried, what worked, and the final solution.
3. **Cross-session**: A shared local SQLite database means knowledge from any session is available to all others.

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

# 2. Register MCP server (run once)
claude mcp add --scope user engram_mcp_server -- $(which engram_mcp_server)
```

Claude Code manages the server lifecycle automatically via stdio — no manual server management needed.

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_keyword_index` | List all keywords in the knowledge base |
| `query_knowledge` | Search by keywords |
| `get_recent_knowledge` | Get N most recent entries |
| `save_knowledge` | Save a learning from the current session |

## License

MIT
