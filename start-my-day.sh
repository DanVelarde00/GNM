#!/usr/bin/env bash
# start-my-day — launch the GNM dashboard + processor
# Usage: ./start-my-day.sh  (or alias it: alias start-my-day='~/path/to/GNM/start-my-day.sh')

set -e
cd "$(dirname "$0")"

# Load .env if present (sets GNM_VAULT_PATH etc.)
[ -f .env ] && export $(grep -v '^#' .env | xargs)

echo "Starting GNM..."

# Use conda env if available, otherwise fall back to plain python
if command -v conda &>/dev/null && conda env list | grep -q base-dev; then
    PYTHON="conda run -n base-dev python"
else
    PYTHON="python"
fi

# Start server in background, redirect logs to a temp file
LOG_FILE="/tmp/gnm-server.log"
$PYTHON server.py --dev > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "Server started (PID $SERVER_PID). Logs: $LOG_FILE"

# Wait until the API is ready (up to 15s)
echo -n "Waiting for server"
for i in $(seq 1 15); do
    sleep 1
    echo -n "."
    if curl -sf http://localhost:8000/api/files/projects > /dev/null 2>&1; then
        echo " ready."
        break
    fi
done

# Open dashboard in default browser (macOS)
if command -v open &>/dev/null; then
    open http://localhost:3000
elif command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:3000
fi

echo "GNM is running. To stop: kill $SERVER_PID"
