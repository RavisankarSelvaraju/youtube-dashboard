#!/bin/sh

# Ensure screen is installed
if ! command -v screen >/dev/null 2>&1; then
  echo "screen is not installed. Installing..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y screen
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y screen
  else
    echo "Could not auto-install screen. Please install screen manually."
    exit 1
  fi
fi

# Run python script inside a detached screen session
if [ -f ./*/bin/activate ]; then
  screen -dmS "yt_tracker" sh -c "source ./*/bin/activate && python3 run.py"
  echo "App started in background screen session named 'yt_tracker'."
  echo "Use 'screen -r yt_tracker' to view logs or attach."
else
  echo "Virtual env does not exist. Run \`bash setup.bash\` first."
fi