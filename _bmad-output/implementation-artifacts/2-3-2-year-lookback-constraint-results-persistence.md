---
story_id: '2.3'
story_key: '2-3-2-year-lookback-constraint-results-persistence'
epic_num: 2
story_num: 3
title: '2-Year Lookback Constraint & Results Persistence'
status: 'done'
---

# Story 2.3: 2-Year Lookback Constraint & Results Persistence

## User Story
**As a** Trader,
**I want** my backtest results to be reliably saved and accessible for later review, with a sensible 2-year data limit to ensure fast processing,
**So that** I don't experience timeouts and can always revisit my past strategy reports.

## Acceptance Criteria
1. **Given** a backtest request for "5 years" of data
   **When** the job starts
   **Then** it automatically truncates the period to the last 2 years
2. **Given** a completed backtest job
   **When** the execution finishes
   **Then** the output (CSV/JSON/Plots) is saved to the shared `/runs/` directory for retrieval
3. **Given** a data loader request
   **When** data is requested
   **Then** only a maximum of 2 years of historical data is loaded

## Tasks / Subtasks

- [x] Task 1: Enforce 2-Year Data Limit (AC: 1, 3)
  - [x] Subtask 1.1: Modify `agent/src/worker.py` to calculate the effective start date (max 2 years back) from the current timestamp.
  - [x] Subtask 1.2: Pass the truncated date range to the data loader fetch calls.
- [x] Task 2: Results Persistence (AC: 2)
  - [x] Subtask 2.1: Ensure backtest CSV results are saved to `runs/{job_id}/{symbol}.csv`.
  - [x] Subtask 2.2: Save a `metadata.json` for each run containing parameters and data summary.
  - [x] Subtask 2.3: Ensure the `RUNS_DIR` mount point is used correctly for container persistence.
- [x] Task 3: Implementation Verification (AC: 1, 2, 3)
  - [x] Subtask 3.1: Add unit tests to verify that dates older than 2 years are truncated correctly.
  - [x] Subtask 3.2: Add tests to verify that files are correctly written to the `/runs/` directory.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Data Constraints:**
  - Standardizing "2 years" as **730 days** or using a calendar-aware delta if possible.
- **Persistence:**
  - Files must be saved in a structure that allows the frontend to retrieve them via the `job_id`.
- **Performance:**
  - Truncating data reduces memory pressure on the Celery workers during backtest execution.

### References
- [Source: _bmad-output/planning-artifacts/architecture.md#4. Persistence & File Storage]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3: 2-Year Lookback Constraint & Results Persistence]

## Dev Agent Record

### Agent Model Used
Gemini 1.5 Pro

### Debug Log References
- Fixed TypeError in Unit Tests by using `.__wrapped__.__func__` to bypass bound Celery task wrappers.

### Completion Notes List
- Enforced 2-year lookback constraint in `agent/src/worker.py`.
- Integrated `matplotlib` for basic price plotting as requested in Code Review.
- Fixed Division by Zero and cumulative penalty bugs in DEX simulation.
- All 21 tests pass 100%.

### File List
- `agent/src/worker.py`
- `agent/tests/unit/test_worker.py`

### Change Log
- Refactored `run_backtest_job` to include file creation processes and metadata export.
- Adjusted validation assertions in test framework to cover file existence.

---
**Status:** done

### Review Findings
- [x] [Review][Decision] Missing Plots Persistence — AC 2 requires plots (CSV/JSON/Plots), but only CSV/JSON are currently saved. Define if we need plots now?
- [x] [Review][Patch] Potential Division by Zero in fee_impact [agent/src/worker.py:182]
- [x] [Review][Patch] Cumulative Fee Penalty on Vector — Fees subtracted from entire returns array [agent/src/worker.py:184]
- [x] [Review][Patch] Relative Path for RUNS_DIR — violates absolute path mount point requirement [agent/src/worker.py:131]
- [x] [Review][Patch] Inaccurate 2-Year Constraint — uses fixed 730 days instead of calendar-aware delta [agent/src/worker.py:94]
- [x] [Review][Patch] Unsafe Type Casting to float for simulator parameters [agent/src/worker.py:180]
- [x] [Review][Patch] Hardcoded DEX identification logic [agent/src/worker.py:65]
- [x] [Review][Defer] Static Gas Fee Assumption [agent/src/worker.py:180] — deferred, outside scope of current stories
- [x] [Review][Defer] Missing Storage Limit/Safety check — deferred, pre-existing architectural concern
