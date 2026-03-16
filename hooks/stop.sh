#!/bin/bash
# Engram Stop hook
# Called by Claude Code every time Claude finishes responding.
# Sends session info to engram server for turn tracking & extraction.

set -euo pipefail

INPUT=$(cat)

# Prevent infinite loops — if stop hook already fired, bail
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // "false"')
if [ "$STOP_ACTIVE" = "true" ]; then
    exit 0
fi

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')

# Send to engram server (fail silently if server not running)
curl -s --max-time 10 \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"transcript_path\": \"$TRANSCRIPT_PATH\"}" \
    "http://localhost:7777/hooks/stop" > /dev/null 2>&1 || true

exit 0
