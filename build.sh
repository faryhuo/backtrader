#!/bin/bash
# Build script for macOS/Linux
# Installs dependencies, builds frontend, and copies static files to backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -f "$ROOT/venv_new/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$ROOT/venv_new/bin/activate"
elif [ -f "$ROOT/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$ROOT/venv/bin/activate"
else
    echo "Warning: Virtual environment not found."
    echo "Continuing with system Python..."
fi

# Install backend dependencies
cd "$ROOT/backend" || exit 1
echo "Installing backend dependencies..."
python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Backend dependency install failed."
    exit 1
fi

# Install frontend dependencies and build
cd "$ROOT/frontend" || exit 1

echo "Installing frontend dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "npm install failed."
    exit 1
fi

echo "Building frontend..."
npm run build
if [ $? -ne 0 ]; then
    echo "Frontend build failed."
    exit 1
fi

# Copy build artifacts to backend
DEST="$ROOT/backend/resources/frontend"
mkdir -p "$DEST"

echo "Copying build artifacts to backend resources..."
rsync -av --delete "$ROOT/frontend/dist/" "$DEST/"
if [ $? -ne 0 ]; then
    # Fallback to cp if rsync is not available
    rm -rf "$DEST"/*
    cp -R "$ROOT/frontend/dist/"* "$DEST/"
fi

echo "Build complete. Static files are in $DEST."
