---
story_id: '2.3'
story_key: '2-3-2-year-lookback-constraint-results-persistence'
epic_num: 2
story_num: 3
title: '2-Year Lookback Constraint & Results Persistence'
status: 'in-progress'
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

- [x] Task 1: Enforce 2-Year Lookback Constraint
  - [x] Subtask 1.1: Modify payload parsing or data loading in `agent/src/worker.py` to truncate any start date that is older than 2 years from the current date.
  - [x] Subtask 1.2: Ensure the truncation logs a warning/info message for the user.
- [x] Task 2: Implement Results Persistence
  - [x] Subtask 2.1: Implement logic to save the results of the backtest (which are pandas dataframes or dictionaries) to CSV/JSON files.
  - [x] Subtask 2.2: Ensure the results are saved in a predictable path within a shared `/runs/` directory (e.g. `/runs/{job_id}/`).
- [x] Task 3: Testing and Validation
  - [x] Subtask 3.1: Add unit tests to verify that dates older than 2 years are truncated correctly.
  - [x] Subtask 3.2: Add tests to verify that files are correctly written to the `/runs/` directory.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Architecture Constraints:**
  - *Data Volume:* Limit the maximum data lookback to 2 years to prevent out-of-memory errors and timeout issues. The logic should ideally be applied before or during the CCXT fetch.
  - *Storage Path:* The PRD mentions saving output to a shared `/runs/` directory. Ensure the path is configurable via environment variables (e.g., `RUNS_DIR` with a fallback to `./runs`).
- **Previous Learnings (from Story 2.2):**
  - Story 2.2 implemented `ccxt` loaders and basic rate-limiting retries. We need to apply the date constraint before passing parameters to `loader.fetch()`.
  - Ensure the output serialization does not block the Celery worker unnecessarily. Use standard python file I/O or pandas `to_csv`/`to_json`.
- **Technical specifics:**
  - Calculate the 2-year boundary using `datetime.now(timezone.utc) - timedelta(days=2*365)`.
  - Handle edge cases where the requested `end_date` is older than 2 years (this might be an invalid state, but we should handle it gracefully).

### Project Structure Notes
- **Suggested Location:** 
  - `agent/src/worker.py` (Update `run_backtest_job` implementation for date truncation and result persistence)
  - `agent/tests/unit/test_worker.py` (Integration tests for 2-year truncation and file writing)

### References
- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3: 2-Year Lookback Constraint & Results Persistence]

## Dev Agent Record

### Agent Model Used
Antigravity (DeepMind)

### Completion Notes List
- Enforced 2-year (730 days) lookback constraint by dynamically determining an `effective_range` limit.
- Maintained tracking for requested range versus effective range in metadata logging.
- Created `RUNS_DIR` path generation matching `{job_id}` structure.
- Implemented file persistence: saving fetched OHLCV DataFrames directly to `.csv` and producing a `metadata.json` describing the job details.
- Verified test coverage via rewritten integration tests that simulate `tmp_path` environment variables matching implementation logic.

### File List
- `agent/src/worker.py`
- `agent/tests/unit/test_worker.py`

### Change Log
- Refactored `run_backtest_job` to include file creation processes and metadata export.
- Adjusted validation assertions in test framework to cover file existence.

---
**Status:** review

