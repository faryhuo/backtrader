#!/bin/bash
# Optimized Docker build script for slow network environments

echo "=== Starting optimized Docker build ==="
echo ""

# Step 1: Build with BuildKit for better caching
echo "[1/3] Building with BuildKit cache..."
DOCKER_BUILDKIT=1 docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --progress=plain \
  -t backtrader-app:latest \
  -f Dockerfile \
  .

if [ $? -ne 0 ]; then
  echo "Build failed!"
  exit 1
fi

echo ""
echo "Build completed successfully!"
echo ""
echo "To run the container:"
echo "  docker-compose up"
echo "  or"
echo "  docker run -p 8020:8000 backtrader-app:latest"
