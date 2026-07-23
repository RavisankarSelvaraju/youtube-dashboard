#!/bin/bash

SESSION="youtube_tracker"

if [ -f ./*/bin/activate ]; then
    # Activate the virtual environment
    source ./*/bin/activate

    # Use tmux if it's installed
    if command -v tmux >/dev/null 2>&1; then
        # Don't start another instance if it's already running
        if tmux has-session -t "$SESSION" 2>/dev/null; then
            echo "Session '$SESSION' is already running."
            exit 0
        fi

        tmux new-session -d -s "$SESSION" "python3 run.py"
        echo "Started in tmux session '$SESSION'."
        echo "Attach with: tmux attach -t $SESSION"
    else
        echo "tmux not found. Running in the current terminal..."
        exec python3 run.py
    fi
else
    echo "Virtual environment does not exist. Run \`bash setup.bash\` first."
fi