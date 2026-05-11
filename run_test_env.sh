#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/agent"
export JWT_SECRET="test_secret_for_local_dev"
export ALLOWED_IPS="127.0.0.1"
export API_AUTH_KEY=""

# Load the virtualenv
source .venv/bin/activate

echo "Starting Celery workers..."
celery -A src.worker.celery_app worker --loglevel=info -n premium@%h -Q backtest.premium,rl_optimization.premium > celery_premium.log 2>&1 &
PREMIUM_PID=$!

celery -A src.worker.celery_app worker --loglevel=info -n standard@%h -Q backtest.standard,rl_optimization.standard,default > celery_standard.log 2>&1 &
STANDARD_PID=$!

echo "Starting API Server..."
uvicorn agent.api_server:app --port 8000 > api.log 2>&1 &
API_PID=$!

echo "Waiting for services to boot (5 seconds)..."
sleep 5

echo "Running Python test script..."
python agent/test_tiered_api.py

echo "--- CELERY PREMIUM LOG ---"
cat celery_premium.log | grep -E "Received task|premium" | tail -n 10

echo "--- CELERY STANDARD LOG ---"
cat celery_standard.log | grep -E "Received task|standard" | tail -n 10

echo "Cleaning up..."
kill $PREMIUM_PID $STANDARD_PID $API_PID
wait $PREMIUM_PID $STANDARD_PID $API_PID 2>/dev/null
echo "Done."
