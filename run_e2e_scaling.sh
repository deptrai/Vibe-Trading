#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/agent"
source .venv/bin/activate

echo "Ensuring clean Redis..."
redis-cli flushall

echo "Seeding Redis queue and old artifacts..."
python agent/test_e2e_scaling_seed.py

echo "Starting Autoscaler in background..."
# Run the autoscaler and capture its logs
export AUTOSCALER_INTERVAL=5
export AUTOSCALER_QUEUE_THRESHOLD=10
python agent/src/autoscaler.py > autoscaler.log 2>&1 &
AUTOSCALER_PID=$!

echo "Waiting for autoscaler to react to the queue length (15 seconds)..."
sleep 15

echo "Autoscaler Log:"
cat autoscaler.log

echo "Checking number of running Celery processes..."
ps aux | grep celery | grep autoscale_ || echo "No autoscale workers found"

echo "Triggering Cleanup via Celery Beat isn't instant. We'll invoke it manually via python for E2E..."
python -c "
from agent.src.cleanup import cleanup_runs_directory
import os
deleted = cleanup_runs_directory('/tmp/vibe-trading/runs')
print(f'E2E Cleanup Deleted: {deleted}')
"

echo "Cleaning up..."
kill $AUTOSCALER_PID
pkill -f celery || true
wait $AUTOSCALER_PID 2>/dev/null
echo "Done."
