---
story_id: '2.1'
story_key: '2-1-async-job-queue-with-redis-celery'
epic_num: 2
story_num: 1
title: 'Async Job Queue with Redis/Celery'
status: 'ready-for-dev'
---

# Story 2.1: Async Job Queue with Redis/Celery

## User Story
**As a** Trader,
**I want** my heavy backtest jobs to be processed in the background without freezing the chat interface,
**So that** I can continue interacting with the AI assistant or submit other tasks while waiting for results.

## Acceptance Criteria
1. **Given** a backtest request from Nowing
   **When** the API receives the request
   **Then** it enqueues a job to Redis and returns a unique `job_id` immediately
2. **Given** a queued job
   **When** a background Celery worker becomes available
   **Then** it picks up the job for execution
3. **Given** the system is running
   **When** multiple job types are submitted
   **Then** tasks are routed to their appropriate queues (e.g., `backtest`)

## Tasks / Subtasks

- [x] Task 1: Setup Celery and Redis Integration (AC: 1, 2)
  - [x] Subtask 1.1: Configure Celery application with Redis as broker and backend in `agent/src/worker.py` (or similar file).
  - [x] Subtask 1.2: Add Celery configuration settings to `.env.example` and load them securely.
- [x] Task 2: Implement Background Task Enqueueing (AC: 1, 3)
  - [x] Subtask 2.1: Create a Celery task function `run_backtest_job(payload: dict)` that accepts the serialized `VibeTradingJobPayload`.
  - [x] Subtask 2.2: Update the `POST /jobs` endpoint in `agent/api_server.py` to enqueue the `run_backtest_job` task asynchronously via Celery instead of just returning a mocked ID.
  - [x] Subtask 2.3: Ensure the API responds immediately with the Celery `task_id` mapped to `job_id`.
- [x] Task 3: Infrastructure and Routing (AC: 2, 3)
  - [x] Subtask 3.1: Define specific queues in Celery config (e.g., `backtest` queue).
  - [x] Subtask 3.2: Provide a script or documentation on how to start the Celery worker process.
- [x] Task 4: Testing and Validation (AC: 1, 2)
  - [x] Subtask 4.1: Write integration tests mocking the Celery task delay to verify the `/jobs` endpoint returns the expected `job_id`.
  - [x] Subtask 4.2: Ensure the API endpoint latency remains < 500ms since the job is processed asynchronously.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Architecture Constraints:**
  - *Broker & State Backend:* Redis is used for high-throughput, reliable task queueing. It ensures jobs are not lost if an execution worker crashes mid-task.
  - *Workers:* Auto-scaling Celery workers picking up asynchronous jobs.
  - *Task Types:* Separated into queues (e.g., `backtest`, `rl_optimization`, `knowledge_graph_sync`, `monte_carlo_stress_test`).
- **Framework Rules:** 
  - Ensure compatibility with FastAPI and Pydantic v2. When passing the `VibeTradingJobPayload` to Celery, serialize it using `.model_dump()` or `.model_dump_json()` since Celery tasks expect serializable arguments (JSON serializer preferred).
- **Previous Learnings:**
  - Story 1.2 set up the `VibeTradingJobPayload` schema. Ensure the enqueued payload uses this strict schema.
  - Story 1.1 established the security requirements. Celery workers do not need `API_AUTH_KEY` checks internally, but the entry point `/jobs` already has `Depends(require_auth)`.
  
### Project Structure Notes
- **Suggested Location:** 
  - `agent/src/worker.py` or `agent/src/celery_app.py` for Celery configuration and tasks.
  - `agent/api_server.py` for API integration.

### References
- [Source: _bmad-output/planning-artifacts/architecture.md#3. Redis/Celery Implementation]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1: Async Job Queue with Redis/Celery]

## Dev Agent Record

### Agent Model Used
(To be filled by dev agent)

### Debug Log References
(To be filled by dev agent)

### Completion Notes List
- Set up Celery app with Redis broker in `agent/src/worker.py`.
- Added REDIS_URL to `.env.example` and requirements.txt updated.
- Created `run_backtest_job` background task assigned to the `backtest` queue.
- Updated `POST /jobs` endpoint to enqueue the task and return `task.id` as `job_id`.
- Created `agent/start_worker.sh` for starting the Celery worker process.
- Created integration test `test_async_job.py` mocking Celery and verifying latency < 500ms.

### File List
- `agent/requirements.txt`
- `agent/.env.example`
- `agent/api_server.py`
- `agent/src/worker.py`
- `agent/start_worker.sh`
- `agent/tests/test_async_job.py`
- `agent/tests/test_payload_validation.py`

### Change Log
- Added asynchronous job queue infrastructure.
- Added background task processing endpoints.

---
**Status:** done

### Review Findings
- [x] [Review][Patch] Unsafe Environment Variable Parsing [agent/start_worker.sh:6]
- [x] [Review][Patch] Synchronous blocking call (`apply_async`) in async route [agent/api_server.py:1189]
- [x] [Review][Patch] Global Module Mocking Pollution for Celery [agent/tests/test_async_job.py:3]
- [x] [Review][Patch] Inline Import Anti-Pattern & Conflicting Module Paths [agent/api_server.py:1188]
- [x] [Review][Patch] Flaky Time-based Assertion in Tests [agent/tests/test_async_job.py:48]
- [x] [Review][Patch] Unhandled Broker Connection Errors [agent/api_server.py:1189]
- [x] [Review][Patch] Missing Task Retry & Failure State [agent/src/worker.py:25]
- [x] [Review][Defer] Missing Rate Limiting for Resource-Intensive Queues [agent/api_server.py:1185] — deferred, pre-existing / out of scope
- [x] [Review][Defer] Large payload bloating Redis broker [agent/api_server.py:1189] — deferred, payload is currently small configuration only
y
