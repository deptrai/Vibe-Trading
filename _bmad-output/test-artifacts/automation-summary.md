---
stepsCompleted:
  - step-01-preflight-and-context
  - step-02-identify-targets
  - step-03c-aggregate

- **Detected Stack:** Backend (`FastAPI`, `Celery`, `Redis`)
- **Execution Mode:** BMad-Integrated (Story 5-3)
- **Loaded Context:**
  - `5-3-automated-cleanup-scaling-policy.md`
  - `agent/src/autoscaler.py`
  - `agent/src/cleanup.py`
  - `agent/tests/unit/test_autoscaler.py`
  - `agent/tests/unit/test_cleanup.py`

# Identify Automation Targets

## 1. Determine Targets

Based on the implemented features for Story 5.3:
- **Unit Tests:** `test_cleanup.py` and `test_autoscaler.py` already provide 100% unit coverage for the newly implemented logic.
- **Integration/E2E Tests:** Currently, there is only a manual E2E bash script (`run_e2e_scaling.sh`). An automated integration test suite using `pytest` is required to integrate this into the CI/CD pipeline and verify the Celery worker and Redis interactions programmatically without relying on bash scripts and manual string parsing.

## 2. Choose Test Levels

- **Integration (P0):** Verify `autoscaler.py` interacting with a real/mocked local Redis instance and properly spawning `celery worker` processes.
- **Integration (P1):** Verify that the `cleanup_runs_directory` is correctly triggered by Celery Beat and actually clears the target directory.

## 3. Assign Priorities

- **P0:** Autoscaling metrics integration (ensuring `LLEN` correctly fetches lengths from real queues and triggers subprocesses).
- **P1:** Cleanup cron job execution inside the Celery environment.

## 4. Coverage Plan

| Target Component | Test Level | Priority | Justification |
|------------------|------------|----------|---------------|
| `autoscaler.py` Redis Polling | Integration | P0 | Critical path for NFR6. Needs to interact with an actual Redis queue to prevent serialization/KeyError issues seen in manual E2E. |
| `autoscaler.py` Process Mgmt | Integration | P0 | Ensures `subprocess.Popen` creates actual workers and kills them gracefully on scale-down. |
| `worker.py` Celery Beat | Integration | P1 | Ensures the beat schedule correctly routes and executes the `run_cleanup` task in an active cluster. |

# Validation & Execution Summary

## Test Generation
- **Subagent Execution Mode:** SEQUENTIAL (API then dependent workers)
- **Detected Stack:** `fullstack`
- **Output:** Skipped API and E2E subagents (no frontend routes/APIs in scope), launched Backend subagent for integration tests.

## Statistics
- **Total Tests Generated:** 4
  - **Backend Integration Tests:** 4
- **Test Levels Covered:** Integration
- **Fixtures Required:** `mock_redis`, `mock_subprocess`
- **Priority Coverage:**
  - P0: 2
  - P1: 2
  - P2: 0
  - P3: 0

## Files Created
- `agent/tests/integration/test_autoscaler_redis.py`
- `agent/tests/integration/test_cleanup_beat.py`

## Key Assumptions and Risks
- **Assumptions:** Redis queue thresholds will be correctly mapped to Redis list lengths (`LLEN`) as simulated by the mocks.
- **Risks:** Directly mocking `subprocess.Popen` means the tests are blind to OS-level child process behavior (e.g. orphan processes). For stronger verification, E2E scaling should run continuously on staging.

## Next Recommended Workflow
Run the **trace** workflow to verify traceability coverage mapping back to NFRs.
