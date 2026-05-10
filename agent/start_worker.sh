#!/bin/bash
# Start the Celery worker for Vibe-Trading background jobs

# Load environment variables if present
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Ensure Python path is set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Celery worker targeting the 'backtest' and 'default' queues
echo "Starting Vibe-Trading Celery Worker..."
celery -A src.worker.celery_app worker --loglevel=info -Q backtest,default
