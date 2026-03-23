#!/usr/bin/env bash
# Start the ECBA Board Showcase Streamlit app
# Usage: bash scripts/start_board_showcase.sh [port]

set -euo pipefail

PORT="${1:-8502}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT"

echo "Starting ECBA Board Showcase on port $PORT..."
echo "URL: http://localhost:$PORT"
echo ""

streamlit run apps/board_showcase.py \
  --server.port "$PORT" \
  --server.headless true \
  --browser.gatherUsageStats false
