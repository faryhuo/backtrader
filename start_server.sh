#!/bin/bash
# Production server startup script for macOS/Linux
# Starts the FastAPI backend server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR/backend" || exit 1

# Set default values if not already set
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "Starting FastAPI server on port $PORT with log level $LOG_LEVEL..."
python main.py
