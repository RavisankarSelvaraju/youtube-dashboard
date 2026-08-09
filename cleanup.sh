#!/usr/bin/env bash
# Tears down youtube-dashboard: kills the tmux session started by run.bash,
# and as a final fallback kills whatever is still bound to the server's port.
# run.bash doesn't track PIDs in a file (unlike camera-server/screen-time-
# dashboard's run.sh), so this only has the tmux session and the port to go on.
set -uo pipefail

SESSION_NAME="youtube_tracker"
PORT=8000

did_something=0

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Killing tmux session '$SESSION_NAME'..."
    tmux kill-session -t "$SESSION_NAME"
    did_something=1
fi

port_pids="$(lsof -ti tcp:"$PORT" 2>/dev/null || true)"
if [ -n "$port_pids" ]; then
    echo "Killing stragglers still bound to port $PORT: $port_pids"
    kill -KILL $port_pids 2>/dev/null || true
    did_something=1
fi

if [ "$did_something" -eq 0 ]; then
    echo "Nothing to clean up: no tmux session, port $PORT is free."
else
    echo "Cleanup complete."
fi
