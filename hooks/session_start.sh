#!/bin/bash
# Engram SessionStart hook
# Called by Claude Code on session start/resume/clear/compact.
# Fetches knowledge context from engram server and prints to stdout
# (stdout is injected into Claude's context).

set -euo pipefail

INPUT=$(cat)
SOURCE=$(echo "$INPUT" | jq -r '.source // "startup"')

# Only load on startup or resume, skip compaction/clear
if [[ "$SOURCE" != "startup" && "$SOURCE" != "resume" ]]; then
    exit 0
fi

# Fetch context from engram server (fail silently if server not running)
RESPONSE=$(curl -s --max-time 5 \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$INPUT" \
    "http://localhost:7777/hooks/session-start" 2>/dev/null) || exit 0

# Print response — this gets injected into Claude's context
if [ -n "$RESPONSE" ]; then
    echo "$RESPONSE"
fi

exit 0
