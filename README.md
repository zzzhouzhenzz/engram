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

> Coming soon — project is under active development.

## License

MIT
