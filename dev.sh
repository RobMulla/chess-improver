#!/bin/bash

# dev.sh - Start the full development stack

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

echo "🚀 Starting Chess Improver Development Stack..."

# 1. Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "📦 Starting Redis..."
    redis-server &
    PID_REDIS=$!
else
    echo "✅ Redis already running"
fi

# Activate virtualenv
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

# 2. Start Worker
echo "👷 Starting Worker..."
rq worker &
PID_WORKER=$!

# 3. Start Web App
echo "🌐 Starting Web App..."
python -m src.web.app &
PID_WEB=$!

# Wait for all processes
wait
