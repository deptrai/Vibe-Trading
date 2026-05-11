---
story_id: '5.3'
story_key: '5-3-automated-cleanup-scaling-policy'
epic_num: 5
story_num: 3
title: 'Automated Cleanup & Scaling Policy'
status: 'ready-for-dev'
---

# Story 5.3: Automated Cleanup & Scaling Policy

Status: ready-for-dev

## Story

As a Premium User,
I want the execution platform to automatically scale up its processing power during high traffic,
So that my complex backtests and Monte Carlo simulations always complete within the SLA timeframe regardless of system load.

## Acceptance Criteria

1. **Automated Cleanup (Cron Job):**
   - **Given** a disk usage threshold of 80% or artifacts older than 7 days in the shared `/runs/` directory
   - **When** the cleanup cron job runs (or background task)
   - **Then** it deletes old job artifact files safely to free up space

2. **Auto-scaling Workers:**
   - **Given** heavy traffic causing the queue depth (e.g. `backtest.standard` or `rl_optimization`) to exceed 10 jobs
   - **When** the autoscaling metric checks the queue length
   - **Then** the system scales up additional Celery worker processes dynamically
   - **And** scales down when the queue depth drops below a safe threshold

3. **Error Path (Fail-Safe Cleanup):**
   - **Given** a file deletion fails mid-cleanup (e.g., permission error or NFS timeout)
   - **When** the cron job encounters the error
   - **Then** it logs the failed path and continues cleaning remaining files
   - **And** partial cleanup is acceptable; the job does NOT abort entirely

## Tasks / Subtasks

- [ ] **Task 1: Automated Cleanup Script (`agent/src/cleanup.py` or equivalent)**
  - [ ] Subtask 1.1: Create a script/task that scans the `/runs/` directory for files older than 7 days.
  - [ ] Subtask 1.2: Check disk usage of the `/runs/` mount; if > 80%, optionally delete files starting from the oldest until usage is below threshold.
  - [ ] Subtask 1.3: Ensure `try/except` around the `os.remove` or `shutil.rmtree` calls to handle permission errors gracefully, logging the failure without crashing the loop.
  - [ ] Subtask 1.4: Add this to Celery beat schedule (e.g., running every hour/day) OR as a system cron script in `agent/start_worker.sh`.

- [ ] **Task 2: Auto-scaling Configuration**
  - [ ] Subtask 2.1: Implement a lightweight script or Celery process manager that monitors the Redis queue lengths (`LLEN backtest`, etc.).
  - [ ] Subtask 2.2: Implement logic: if queue > 10, spawn new Celery worker subprocesses (up to a MAX limit). If queue == 0 for X minutes, scale down.
  - [ ] Subtask 2.3: Integrate this scaling policy logic into `agent/start_worker.sh` or a dedicated `agent/src/autoscaler.py` daemon.

- [ ] **Task 3: Unit Testing & Verification**
  - [ ] Subtask 3.1: Write tests for the cleanup logic, mocking `os.stat` and `os.remove` to simulate successful and failed deletions.
  - [ ] Subtask 3.2: Verify the auto-scaling logic calculates queue length thresholds correctly and issues the correct scale commands.

## Dev Notes

### Architecture Compliance
- The WFA, RL, and Monte Carlo workloads generate large numbers of artifacts in `/runs/<job_id>`. Without cleanup, disk will fill quickly. WFA especially creates many CSVs/JSONs per WFA window.
- The 2-year lookback limit (FR6) controls the size of incoming data, but scaling relies on this cleanup logic to keep worker nodes healthy.
- NFR6 explicitly requires auto-scaling when jobs > 10.

### Auto-scaling Implementation
Since the execution engine runs as a set of processes on a VM (or container), "spinning up additional workers" can be implemented via Celery's native autoscaling (`--autoscale=MAX,MIN`) OR by writing a custom autoscaler loop that monitors Redis and runs `subprocess.Popen` for workers. 
If using Celery's built-in autoscale: 
- Update `start_worker.sh` to use `celery -A src.worker worker --autoscale=10,2`. Wait, Celery's `--autoscale` changes the thread/pool size, NOT the number of worker containers. Review whether thread pooling vs subprocess scaling is appropriate. Typically, `--autoscale=MAX,MIN` on a single machine is acceptable for this AC if it meets the need to increase concurrency based on load.

### Cleanup Implementation
A Celery beat task is preferred over system cron to keep all logic inside Python and ensure cross-platform compatibility. Update `beat_schedule` in `agent/src/worker.py` (or `celery_app.py`) to include the cleanup task.

### Project Context Reminders
- Use `logging` instead of `print()`.
- Error paths MUST be robust to avoid crashing the beat scheduler.
- Keep the `RUNS_DIR` path configurable via environment variable `RUNS_DIR`.

## File List
- `agent/src/worker.py` (UPDATE - add beat schedule)
- `agent/src/cleanup.py` (CREATE)
- `agent/start_worker.sh` (UPDATE - add autoscaler options)
- `agent/tests/unit/test_cleanup.py` (CREATE)

## Dev Agent Record
*To be filled by the dev agent upon completion.*
