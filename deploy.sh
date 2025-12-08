#!/usr/bin/env sh
set -euo pipefail

# Root paths
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"

# Ports (override via env)
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

cleanup() {
    # stop child processes on exit
    if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

echo "==> Ensuring backend dependencies"
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    python -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

echo "==> Ensuring frontend dependencies"
cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
    npm install
fi

echo "==> Starting frontend (Vite dev server with API proxy) on :$FRONTEND_PORT"
npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo "==> Starting backend (Uvicorn) on :$BACKEND_PORT"
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" python -m uvicorn api:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"
echo "Backend PID:  $BACKEND_PID"
echo "Press Ctrl+C to stop both."

wait
