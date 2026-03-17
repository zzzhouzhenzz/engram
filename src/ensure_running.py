"""Ensure engram MCP server is running. Starts it if not.

Used as a Claude Code hook (command type) to auto-start the server.
Cross-platform: works on macOS, Linux, and Windows.
"""

import subprocess
import sys
import time

import urllib.request
import urllib.error

HEALTH_URL = "http://localhost:7777/health"
MAX_WAIT = 10  # seconds


def _is_running() -> bool:
    try:
        urllib.request.urlopen(HEALTH_URL, timeout=2)
        return True
    except (urllib.error.URLError, OSError):
        return False


def main():
    if _is_running():
        return

    # Start server as a detached background process
    cmd = [sys.executable, "-m", "engram.server"]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Wait for it to be ready
    deadline = time.monotonic() + MAX_WAIT
    while time.monotonic() < deadline:
        if _is_running():
            return
        time.sleep(0.5)

    print("Warning: engram_mcp_server failed to start", file=sys.stderr)


if __name__ == "__main__":
    main()
