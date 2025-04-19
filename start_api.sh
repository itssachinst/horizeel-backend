#!/bin/bash
echo "Setting environment variables..."
export ENABLE_HTTPS_REDIRECT=false
echo "Starting API server..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 