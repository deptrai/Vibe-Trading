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

# Start Celery workers using dedicated pools.
# Fairness implementation: Dedicated processes guarantee that standard jobs 
# are never fully starved by premium jobs, while premium jobs get more resources.
echo "Starting Vibe-Trading Celery Workers (Dedicated Pools)..."

# Premium worker: dedicated pool for premium jobs
celery -A src.worker.celery_app worker --loglevel=info -n premium@%h --autoscale=10,3 -Q backtest.premium,rl_optimization.premium &

# Standard worker: dedicated pool for standard and default jobs
celery -A src.worker.celery_app worker --loglevel=info -n standard@%h --autoscale=3,1 -Q backtest.standard,rl_optimization.standard,default

wait
