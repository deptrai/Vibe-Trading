---
story_id: '3.4'
story_key: '3-4-walk-forward-analysis-wfa'
epic_num: 3
story_num: 4
title: 'Walk-Forward Analysis (WFA)'
status: 'done'
---

# Story 3.4: Walk-Forward Analysis (WFA)

## Epic 3: AI-Driven Strategy Evolution (RL & Graph)
Tối ưu hóa tham số qua RL và kết nối tri thức qua Knowledge Graph.

## User Story
**As a** Quant Analyst,
**I want** the system to perform Walk-Forward Analysis during strategy optimization,
**So that** I can ensure my strategy works on unseen data and isn't overfitted to the past.

## Acceptance Criteria
1. [x] **Given** a request to optimize a strategy via RL with `wfa_config` provided
   **When** the optimization job runs
   **Then** it splits the historical data into rolling In-sample (train) and Out-of-sample (test) windows
2. [x] **Given** the WFA completes
   **When** results are aggregated
   **Then** it reports the average In-sample score, average Out-of-sample score, and the "Out-of-sample decay rate"
3. [x] **Given** the historical data range is too short
   **When** the WFA job starts
   **Then** it returns an error if fewer than 3 valid windows can be constructed

---

## Developer Context

### Architecture Decision: Rolling Window Generator
We implemented a rolling window generator with overlap to maximize the number of test windows (default target 10-20 windows).

### Implementation Details

#### 1. RLOptimizer Enhancement (`agent/src/rl_optimizer.py`)
- **New Method:** `walk_forward_optimize()`
- **Logic:**
  - Calculates `window_size` and `step_size` based on total data points.
  - Loops through windows:
    - Optimizes parameters on IS range.
    - Evaluates the "best" parameters on the subsequent OOS range.
  - Aggregates performance metrics (IS Mean, OOS Mean, Decay Rate).
  - Performs a final optimization on the entire dataset to provide the current best parameters.

#### 2. Worker Integration (`agent/src/rl_worker.py`)
- Detects `wfa_config` in the execution flags.
- Routes to `walk_forward_optimize` instead of standard `optimize`.
- Suppression of intermediate progress file writes during window loops to save I/O.

#### 3. API Result Retrieval (`agent/api_server.py`)
- New Endpoint: `GET /api/v1/jobs/{job_id}/results`
  - Returns the complete `optimized_params.json` which now includes the `wfa` result block.

### Technical Requirements
```python
# WFA Output Block in optimized_params.json
"wfa": {
    "is_mean_score": float,
    "oos_mean_score": float,
    "decay_rate": float, # (OOS / IS) - 1
    "windows": [
        {
            "window": int,
            "is_range": [start, end],
            "oos_range": [start, end],
            "is_score": float,
            "oos_score": float,
            "decay": float,
            "params": dict
        }
    ]
}
```

---

## Tasks / Subtasks

- [x] Task 1: Enhance RLOptimizer with WFA
  - [x] Subtask 1.1: Implement window splitting logic with overlap support
  - [x] Subtask 1.2: Implement IS optimization loop
  - [x] Subtask 1.3: Implement OOS evaluation logic
  - [x] Subtask 1.4: Implement metrics aggregation and decay calculation

- [x] Task 2: Worker & API Integration
  - [x] Subtask 2.1: Update `rl_worker.py` to trigger WFA mode
  - [x] Subtask 2.2: Implement I/O suppression for sub-optimizations
  - [x] Subtask 2.3: Add `GET /api/v1/jobs/{job_id}/results` endpoint to `api_server.py`

- [x] Task 3: Validation
  - [x] Subtask 3.1: Verify window count and ranges with mock data
  - [x] Subtask 3.2: Verify Decay Rate accuracy
  - [x] Subtask 3.3: Verify "Too short data" error path

---

## File List

| File | Status | Description |
|------|--------|-------------|
| `agent/src/rl_optimizer.py` | MODIFIED | Added WFA core logic |
| `agent/src/rl_worker.py` | MODIFIED | Added WFA routing |
| `agent/api_server.py` | MODIFIED | Added results retrieval endpoint |
| `_bmad-output/implementation-artifacts/3-4-walk-forward-analysis-wfa.md` | CREATED | This artifact |

---

## Change Log

- **2026-05-11:** (Gemini CLI) Story implemented and verified. WFA core logic handles overlapping windows and provides comprehensive decay analysis.
