import os
import json
import redis
import time
import shutil

# Make sure runs dir exists and has some files for cleanup
runs_dir = "/tmp/vibe-trading/runs"
os.makedirs(runs_dir, exist_ok=True)
for i in range(5):
    job_dir = os.path.join(runs_dir, f"old_job_{i}")
    os.makedirs(job_dir, exist_ok=True)
    with open(os.path.join(job_dir, "data.txt"), "w") as f:
        f.write("old data")
    # Set time to 8 days ago
    eight_days_ago = time.time() - (8 * 86400)
    os.utime(job_dir, (eight_days_ago, eight_days_ago))

# Connect to Redis
r = redis.Redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

# Create 15 dummy tasks in the queue directly
from celery import Celery

app = Celery('vibe_trading', broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

print("Pushing 15 tasks to backtest.standard queue via Celery...")
for i in range(15):
    # This will put proper Celery message format in the queue
    # We send it to a dummy name or the real name, since we will kill the workers soon anyway.
    app.send_task("src.worker.run_backtest_job", kwargs={"payload": {}}, queue="backtest.standard")

# Verify
r = redis.Redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))
print(f"Queue length now: {r.llen('backtest.standard')}")
