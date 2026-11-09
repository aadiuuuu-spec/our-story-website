#!/bin/sh
set -eu

PORT="${PORT:-8080}"
BOT_PID=""

if [ -n "${BOT_TOKEN:-}" ] && [ -n "${OWNER_ID:-}" ]; then
    echo "Starting Telegram bot in background..."
    python -u aadi.py &
    BOT_PID=$!
else
    echo "WARNING: BOT_TOKEN or OWNER_ID is missing; website will start, but Telegram bot will stay offline."
fi

cleanup() {
    if [ -n "$BOT_PID" ]; then
        kill "$BOT_PID" 2>/dev/null || true
        wait "$BOT_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

echo "Starting Our Story website on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port "$PORT"
