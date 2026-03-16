#!/bin/bash
# Ensures engram server is running. Starts it if not.
# Called by SessionStart hook before HTTP hooks fire.

set -euo pipefail

HEALTH_URL="http://localhost:7777/health"

# Check if server is already running
if curl -s --max-time 2 "$HEALTH_URL" > /dev/null 2>&1; then
    exit 0
fi

# Start server in background
engram_mcp_server &
disown

# Wait for server to be ready (up to 10s)
for i in $(seq 1 20); do
    if curl -s --max-time 1 "$HEALTH_URL" > /dev/null 2>&1; then
        exit 0
    fi
    sleep 0.5
done

echo "Warning: engram server failed to start" >&2
exit 0
