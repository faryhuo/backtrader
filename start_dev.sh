#!/bin/bash
# Development mode startup script for macOS/Linux
# Starts both backend and frontend development servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"

# Check directories exist
if [ ! -d "$ROOT/backend" ]; then
    echo "Backend directory not found at $ROOT/backend."
    exit 1
fi

if [ ! -d "$ROOT/frontend" ]; then
    echo "Frontend directory not found at $ROOT/frontend."
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping development servers..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Launching backend (port 8000) and frontend dev server (default Vite port 5173)..."

# Start backend server
cd "$ROOT/backend"
python main.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start frontend dev server
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo "Both servers are running. Press Ctrl+C to stop."

# Wait for processes
wait
