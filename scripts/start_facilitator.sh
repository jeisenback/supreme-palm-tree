#!/usr/bin/env bash
set -euo pipefail

# Activate virtualenv if present (.venv created by repo)
if [ -f .venv/Scripts/activate ]; then
  # Windows-style venv in Git Bash or WSL
  source .venv/Scripts/activate
elif [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

echo "Installing requirements..."
pip install -r requirements.txt

export STREAMLIT_SERVER_HEADLESS=true

: ${PORT:=8501}
echo "Starting Streamlit on port ${PORT}..."
streamlit run apps/facilitator_ui.py --server.port ${PORT} --server.address 0.0.0.0
