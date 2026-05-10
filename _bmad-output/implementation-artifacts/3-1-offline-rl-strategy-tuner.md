---
story_id: '3.1'
story_key: '3-1-offline-rl-strategy-tuner'
epic_num: 3
story_num: 1
title: 'Offline RL Strategy Tuner'
status: 'in-progress'
---

# Story 3.1: Offline RL Strategy Tuner

## Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.

## User Story
**As a** Trader,
**I want** the system to automatically suggest the best parameters for my strategy using Reinforcement Learning,
**So that** my strategy can adapt to different market phases without me being a math expert.

## Acceptance Criteria
1. **Given** a base strategy and a historical dataset with `enable_rl_optimization=true`
   **When** I trigger the "Optimize" command via `POST /jobs`
   **Then** a dedicated RL worker (`rl_optimization` queue) runs Optuna trials to find the highest Sharpe ratio
   **And** it returns the optimized parameter set (e.g., `rsi_period: 10` instead of `14`)
2. **Given** the optimization completes
   **When** results are persisted
   **Then** the optimized parameters are saved to `runs/<job_id>/optimized_params.json`
   **And** include trial history, best Sharpe, and improvement delta vs baseline
3. **Given** an RL optimization job is running
   **When** the client polls for status
   **Then** it receives progress updates (current trial / total trials, best score so far)
4. **Given** a job with `enable_rl_optimization=true`
   **When** it is enqueued
   **Then** it is routed to the `rl_optimization` queue, NOT the `backtest` queue

---

## Developer Context

### Architecture Decision: Optuna (v1)
For the initial implementation, use **Optuna** as the optimization engine:
- **Why not stable-baselines3:** Requires PyTorch (~2GB), GPU setup, and `gymnasium` — overkill for parameter tuning
- **Why not custom mutation loop:** No pruning, no visualization, reinventing the wheel
- **Why Optuna:** Lightweight (~50MB), built-in TPE sampler, pruning support, trial history, easy to distribute later

### Technical Requirements

#### 1. New Celery Task & Queue (`rl_optimization`)
- Create a **new file** `agent/src/rl_worker.py` with task `run_rl_optimization_job`
- Register the task route in `worker.py`'s `celery_app.conf.update`:
  ```python
  task_routes={
      "src.worker.run_backtest_job": {"queue": "backtest"},
      "src.rl_worker.run_rl_optimization_job": {"queue": "rl_optimization"},
      "src.worker.*": {"queue": "default"},
  }
  ```
- Celery task config:
  ```python
  @celery_app.task(
      name="src.rl_worker.run_rl_optimization_job",
      bind=True,
      soft_time_limit=1800,   # 30 min soft limit
      time_limit=2100,        # 35 min hard kill
      max_retries=1,
      acks_late=True,
  )
  ```

#### 2. RL Optimization Engine (`RLOptimizer`)
- Create `agent/src/rl_optimizer.py` containing the `RLOptimizer` class
- **Optimization space** (configurable via payload, with sensible defaults):

| Parameter | Type | Range | Default |
|-----------|------|-------|---------|
| `rsi_period` | int | 5–30 | 14 |
| `macd_fast` | int | 8–20 | 12 |
| `macd_slow` | int | 20–40 | 26 |
| `macd_signal` | int | 5–15 | 9 |
| `ma_period` | int | 10–200 | 50 |
| `stop_loss_pct` | float | 0.01–0.10 | 0.05 |
| `take_profit_pct` | float | 0.02–0.20 | 0.10 |

- **Objective function:** For each trial, run a simplified backtest with the sampled params → calculate Sharpe ratio
- **Sharpe calculation:** Use `Decimal` for PnL accumulation, convert to float only for Optuna's minimize/maximize
- **Budget:** Default 50 trials, max 200 trials (configurable via payload)
- **Pruning:** Enable Optuna's `MedianPruner` to early-stop clearly bad trials

#### 3. Payload Handling & API Routing
- In `api_server.py` → `create_job()` endpoint:
  ```python
  if payload.execution_flags.enable_rl_optimization:
      from src.rl_worker import run_rl_optimization_job
      task = await asyncio.to_thread(
          run_rl_optimization_job.apply_async,
          args=[payload.model_dump(mode="json")],
          queue="rl_optimization"
      )
  else:
      # existing backtest routing
  ```
- The `enable_rl_optimization` flag already exists in `api_models.py:L42` ✅
- **New payload fields** (add to `ExecutionFlags`):
  ```python
  rl_max_trials: int = Field(50, ge=10, le=200)
  rl_optimization_target: str = Field("sharpe", pattern=r"^(sharpe|pnl|sortino)$")
  ```

#### 4. Output / Persistence
- Save to `runs/<job_id>/optimized_params.json`:
  ```json
  {
    "status": "completed",
    "best_params": {"rsi_period": 10, "macd_fast": 15, ...},
    "best_score": 1.87,
    "optimization_target": "sharpe",
    "baseline_score": 0.92,
    "improvement_pct": 103.2,
    "total_trials": 50,
    "trial_history": [
      {"trial": 0, "params": {...}, "score": 0.45, "state": "COMPLETE"},
      ...
    ],
    "elapsed_seconds": 342.5
  }
  ```
- Save progress during run to `runs/<job_id>/progress.json`:
  ```json
  {"current_trial": 25, "total_trials": 50, "best_score_so_far": 1.54}
  ```

#### 5. Progress Reporting
- Use `self.update_state(state='PROGRESS', meta={...})` in the Celery task
- Also persist `progress.json` to disk so the file-based polling works even without Celery result backend

### Resource Limits & Guardrails

| Guardrail | Value | Rationale |
|-----------|-------|-----------|
| `soft_time_limit` | 1800s (30min) | Prevent runaway optimization |
| `time_limit` | 2100s (35min) | Hard kill after soft limit grace |
| `max_trials` | 200 | Prevent user from requesting unbounded search |
| `max_retries` | 1 | RL jobs are expensive, don't retry infinitely |
| Memory guard | Check `psutil.virtual_memory()` before each trial | Abort if <500MB free |

### Architecture Compliance
- **Microservice Specialist Worker:** Vibe-Trading is purely an execution engine. It receives the schema and data, performs compute, and saves to `/runs/`.
- **Worker Isolation:** Must use a dedicated queue to satisfy: "The RL workers are deployed in strictly isolated Docker containers."
- **Data Precision:** Use `Decimal` for all PnL and Sharpe ratio calculations to prevent float drift.

---

## Tasks / Subtasks

- [ ] Task 1: Add Dependencies & Payload Extensions
  - [ ] Subtask 1.1: Add `optuna>=3.0` to `pyproject.toml` dependencies
  - [ ] Subtask 1.2: Add `psutil>=5.9` to `pyproject.toml` for memory monitoring
  - [ ] Subtask 1.3: Add `rl_max_trials` and `rl_optimization_target` fields to `ExecutionFlags` in `api_models.py`

- [ ] Task 2: Create RL Optimizer Engine
  - [ ] Subtask 2.1: Create `agent/src/rl_optimizer.py` with `RLOptimizer` class
  - [ ] Subtask 2.2: Implement parameter search space definition (RSI, MACD, MA, SL/TP)
  - [ ] Subtask 2.3: Implement simplified backtest objective function using historical returns
  - [ ] Subtask 2.4: Implement Sharpe/PnL/Sortino calculation with `Decimal` precision
  - [ ] Subtask 2.5: Implement Optuna study with `MedianPruner` and TPE sampler
  - [ ] Subtask 2.6: Implement progress persistence to `progress.json`

- [ ] Task 3: Create RL Worker Task
  - [ ] Subtask 3.1: Create `agent/src/rl_worker.py` with `run_rl_optimization_job` Celery task
  - [ ] Subtask 3.2: Import and reuse `celery_app` from `worker.py` (shared Celery instance)
  - [ ] Subtask 3.3: Add task route `"src.rl_worker.run_rl_optimization_job": {"queue": "rl_optimization"}` to `worker.py` config
  - [ ] Subtask 3.4: Implement data loading (reuse CCXT loader from `worker.py`)
  - [ ] Subtask 3.5: Implement `self.update_state()` for Celery progress reporting
  - [ ] Subtask 3.6: Save `optimized_params.json` to `runs/<job_id>/`
  - [ ] Subtask 3.7: Add memory guard check before each trial batch

- [ ] Task 4: API Routing Integration
  - [ ] Subtask 4.1: Update `api_server.py` `create_job()` to check `enable_rl_optimization` flag
  - [ ] Subtask 4.2: Route RL jobs to `rl_optimization` queue via `run_rl_optimization_job.apply_async`
  - [ ] Subtask 4.3: Add `GET /jobs/{job_id}/progress` endpoint for RL progress polling

- [ ] Task 5: Docker Infrastructure
  - [ ] Subtask 5.1: Add `redis` service to `docker-compose.yml`
  - [ ] Subtask 5.2: Add `rl-worker` service with `celery -A src.worker worker -Q rl_optimization -c 1 --max-memory-per-child=512000`
  - [ ] Subtask 5.3: Set resource limits (`mem_limit: 1g`, `cpus: 2`)

- [ ] Task 6: Testing & Validation
  - [ ] Subtask 6.1: Unit test `RLOptimizer` with mocked returns (5 trials, verify output schema)
  - [ ] Subtask 6.2: Unit test Sharpe calculation accuracy with known data
  - [ ] Subtask 6.3: Unit test parameter bounds enforcement (min/max clipping)
  - [ ] Subtask 6.4: Integration test: payload with `enable_rl_optimization=true` → queued to `rl_optimization`
  - [ ] Subtask 6.5: Integration test: verify `optimized_params.json` schema and content
  - [ ] Subtask 6.6: Edge case test: timeout handling (`SoftTimeLimitExceeded`) → graceful save of best-so-far

---

## File Structure

| File | Action | Description |
|------|--------|-------------|
| `pyproject.toml` | MODIFY | Add `optuna>=3.0`, `psutil>=5.9` |
| `agent/src/api_models.py` | MODIFY | Add `rl_max_trials`, `rl_optimization_target` to `ExecutionFlags` |
| `agent/src/rl_optimizer.py` | CREATE | Optuna-based parameter optimization engine |
| `agent/src/rl_worker.py` | CREATE | Celery task for RL optimization queue |
| `agent/src/worker.py` | MODIFY | Add task route for RL queue |
| `agent/api_server.py` | MODIFY | Conditional routing based on `enable_rl_optimization` flag |
| `agent/tests/unit/test_rl_optimizer.py` | CREATE | Unit tests for optimizer logic |
| `agent/tests/unit/test_rl_worker.py` | CREATE | Integration tests for RL task routing |
| `docker-compose.yml` | MODIFY | Add `redis` + `rl-worker` services |

---

## Dev Notes

### Reusable Patterns from Existing Codebase
- **Data loading:** Reuse `get_loader_cls_with_fallback("ccxt")` pattern from `worker.py:L126-132`
- **Job directory creation:** Reuse `os.makedirs(job_dir, exist_ok=True)` pattern from `worker.py:L146-147`
- **Celery task wrapping for tests:** Use `__wrapped__.__func__` pattern discovered in Story 2-6
- **Financial precision:** Follow `Decimal` pattern from `perpetual_simulator.py`

### Worker Startup Commands
```bash
# Standard backtest worker
celery -A src.worker worker -Q backtest -c 4

# RL optimization worker (isolated, single-concurrency)
celery -A src.worker worker -Q rl_optimization -c 1 --max-memory-per-child=512000
```

### References
- [Architecture: RL Worker Isolation](_bmad-output/planning-artifacts/architecture.md#4-knowledge-graph-rl--monte-carlo-isolation)
- [Epic 3: Story 3.1](_bmad-output/planning-artifacts/epics.md#story-31-offline-rl-strategy-tuner)
- [Existing flag: enable_rl_optimization](agent/src/api_models.py#L42)

## Project Context Reference
- **Tech Stack:** Python 3.11+, FastAPI, Celery, Redis, Pydantic v2, Optuna.
- **Storage:** Shared File System at `/tmp/vibe-trading/runs` (or `RUNS_DIR` env var).
- **Precision:** `Decimal` class for all financial calculations.

## Completion Status
**Status:** ready-for-dev
