import os
from celery import Celery

# Default to localhost Redis if not provided in environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "vibe_trading_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "src.worker.run_backtest_job": {"queue": "backtest"},
        "src.worker.*": {"queue": "default"},
    },
)

@celery_app.task(name="src.worker.run_backtest_job", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def run_backtest_job(self, payload: dict) -> dict:
    """
    Background task to run a backtest job.
    Accepts the serialized VibeTradingJobPayload as a dictionary.
    """
    # TODO: Implement actual backtesting logic here
    import time
    time.sleep(2) # Mocking work
    
    return {
        "status": "success",
        "job_id": self.request.id,
        "message": "Backtest completed (mock)",
        "payload_received": payload
    }
