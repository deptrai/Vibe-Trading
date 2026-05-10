---
story_id: '2.4'
story_key: '2-4-monte-carlo-stress-test'
epic_num: 2
story_num: 4
title: 'Monte Carlo Stress Test'
status: 'in-progress'
---

# Story 2.4: Monte Carlo Stress Test

## User Story
**As a** Risk-Averse Trader,
**I want** the engine to run Monte Carlo simulations (resampling) on my backtest results,
**So that** I can see the probability of "Black Swan" events and extreme drawdowns.

## Acceptance Criteria
1. **Given** a successfully completed backtest job with `enable_monte_carlo_stress_test=true`
   **When** the worker processes the flag
   **Then** it runs 10,000+ resampled paths on the historical trade series
2. **Given** the Monte Carlo simulation finishes
   **When** metrics are calculated
   **Then** it outputs a risk distribution graph data and 95% Confidence Interval metrics

## Tasks / Subtasks

- [x] Task 1: Create Monte Carlo Engine
  - [x] Subtask 1.1: Create `agent/src/monte_carlo.py` to contain the resampling logic.
  - [x] Subtask 1.2: Implement vectorized numpy/pandas logic to generate 10,000 resampled equity curves from a trade series.
  - [x] Subtask 1.3: Calculate metrics: 95% CI Max Drawdown, Risk of Ruin, and Final Capital distribution.
- [x] Task 2: Integrate into Worker
  - [x] Subtask 2.1: Update `agent/src/worker.py` to check `enable_monte_carlo_stress_test` in the payload's `execution_flags`.
  - [x] Subtask 2.2: If true, invoke the Monte Carlo engine passing the backtest's returns/trades.
  - [x] Subtask 2.3: Save the Monte Carlo metrics into the job's `metadata.json` or a separate `monte_carlo.json` within the `/runs/<job_id>` directory.
- [x] Task 3: Testing and Validation
  - [x] Subtask 3.1: Unit tests for `monte_carlo.py` verifying math accuracy and performance with 10k iterations.
  - [x] Subtask 3.2: Integration test in `test_worker.py` ensuring the worker triggers the simulation when the flag is set.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Architecture Constraints:**
  - *Data Volume:* Limit the maximum data lookback to 2 years to prevent out-of-memory errors and timeout issues. The logic should ideally be applied before or during the CCXT fetch.
  - *Storage Path:* The PRD mentions saving output to a shared `/runs/` directory. Ensure the path is configurable via environment variables (e.g., `RUNS_DIR` with a fallback to `./runs`).
- **Technical specifics:**
  - Use `numpy.random.choice` for resampling. Ensure vectorization instead of loops for 10,000 iterations to meet performance requirements.
  - Ensure Decimal or at least `float64` is used to prevent float drift during cumulative product calculations.

### Project Structure Notes
- **Suggested Location:** 
  - `agent/src/worker.py`
  - `agent/src/monte_carlo.py`
  - `agent/tests/unit/test_monte_carlo.py`

### References
- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4: Monte Carlo Stress Test]

## Dev Agent Record

### Agent Model Used
Antigravity (DeepMind)

### Debug Log References
- Addressed DataFrame property assumptions to ensure `empty` and `index` are correctly checked.

### Completion Notes List
- Created `agent/src/monte_carlo.py` to house the `MonteCarloSimulator` class.
- Implemented fast vectorized sampling of 10,000 paths using numpy (`np.random.choice`).
- Calculated key metrics: 95% CI Max Drawdown, Risk of Ruin Probability, and final capital distributions.
- Integrated the simulation step into `agent/src/worker.py` checking the `enable_monte_carlo_stress_test` flag.
- Exported the results explicitly into a dedicated `_monte_carlo.json` file per asset and inside `metadata.json`.
- Created robust unit tests validating the math (`test_monte_carlo.py`).
- Added an integration test in `test_worker.py` ensuring it triggers when the flag is true.

### File List
- `agent/src/monte_carlo.py`
- `agent/src/worker.py`
- `agent/tests/unit/test_monte_carlo.py`
- `agent/tests/unit/test_worker.py`

### Change Log
- Added `monte_carlo.py` engine to calculate probabilities of black swan events.
- Updated Celery worker loop to post-process simulation if enabled.
- Re-formatted test suites to cover Monte Carlo branch paths.

---
**Status:** done

### Review Findings
- [x] [Review][Patch] Memory Exhaustion (OOM) on High-Resolution Data (`simulated_returns = np.random.choice(...)` can crash worker) [`agent/src/monte_carlo.py:43`]
- [x] [Review][Patch] Missing Error Isolation in Worker Loop (Uncaught exceptions crash the job) [`agent/src/worker.py:140`]
- [x] [Review][Patch] Missing Guard for `initial_capital` Validity (Payload property unsafe cast) [`agent/src/worker.py:151`]
- [x] [Review][Patch] Unhandled Infinite Values (`Inf`) in Returns (Breaks JSON dumping) [`agent/src/worker.py:144`]
- [x] [Review][Patch] Negative Equity Corruption (Returns <= -100% causes negative cumulative paths) [`agent/src/monte_carlo.py:47`]
- [x] [Review][Patch] Invalid `iterations` Boundary (0 or negative iterations crash numpy) [`agent/src/monte_carlo.py:18`]
- [x] [Review][Patch] Incorrect Return Data Source (Proxying trades with asset returns violates AC 1) [`agent/src/worker.py:144`]
- [x] [Review][Patch] Missing Risk Distribution Graph Data Output (Missing raw distribution data violates AC 2) [`agent/src/monte_carlo.py:76`]
- [x] [Review][Patch] Deviation from Python Best Practices (In-Loop Inline Imports) [`agent/src/worker.py:147`]
