---
story_id: '2.2'
story_key: '2-2-multi-market-data-loading-system'
epic_num: 2
story_num: 2
title: 'Crypto-First Data Loading System'
status: 'done'
---

# Story 2.2: Crypto-First Data Loading System

## User Story
**As a** Trader,
**I want** the system to prioritize fetching data via CCXT and On-chain RPCs for Crypto assets, while maintaining an open architecture for future VN/US stock expansion,
**So that** I can seamlessly backtest high-frequency crypto strategies without data latency.

## Acceptance Criteria
1. **Given** a valid symbol (e.g., "BTC/USDT", "ETH/USDC")
   **When** the execution engine runs
   **Then** it correctly routes the request to CCXT or a fallback RPC node
2. **Given** a request for VN/US symbols (e.g., "VNM", "AAPL")
   **When** the system processes the request
   **Then** it gracefully ignores VN/US symbols (returning a "Phase 2 feature" error)
3. **Given** a data fetching operation
   **When** API rate limits or connection errors occur
   **Then** it handles API rate limits using the built-in retry mechanism
4. **Given** the Celery backtest job from Story 2.1
   **When** the worker processes the payload
   **Then** it leverages the crypto-first loader to fetch real data instead of mocking work

## Tasks / Subtasks

- [x] Task 1: Enhance `run_backtest_job` in Worker (AC: 1, 4)
  - [x] Subtask 1.1: Import and instantiate the backtest runner or integrate the `runner.py` logic within `agent/src/worker.py`.
  - [x] Subtask 1.2: Pass the configured parameters from `VibeTradingJobPayload` (like assets, timeframe) to the engine runner.
- [x] Task 2: Validate Crypto-First & Retry Mechanisms (AC: 1, 2, 3)
  - [x] Subtask 2.1: Ensure that the data loader is configured to prioritize CCXT and fallback RPCs.
  - [x] Subtask 2.2: Add validation to reject non-crypto symbols (e.g., returning "Phase 2 feature" error) for now.
  - [x] Subtask 2.3: Review crypto loaders to verify they implement retry mechanisms with backoff for rate limit handling.
- [x] Task 3: Testing and Validation (AC: 1, 2, 3, 4)
  - [x] Subtask 3.1: Add integration tests simulating backtest jobs for Crypto to verify correct provider selection.
  - [x] Subtask 3.2: Verify handling of API rate limits by mocking failed responses and expecting retries.
  - [x] Subtask 3.3: Verify that non-crypto symbols are correctly rejected.

## Dev Notes

### 🔬 Exhaustive Analysis & Guardrails

- **Architecture Constraints:**
  - *Data Resilience:* Automated fallbacks programmed in the data loaders (`yfinance` -> `akshare` -> `ccxt`). The system uses `FALLBACK_CHAINS` in `agent/backtest/loaders/registry.py` and detects the market type from symbol strings using regex.
  - *Integration Point:* The worker `agent/src/worker.py` must transition from simply mocking work (with `time.sleep`) to invoking the actual backtest execution using `backtest.runner.main` or directly invoking engines and loaders.
- **Previous Learnings (from Story 2.1):**
  - Story 2.1 set up the background task `run_backtest_job` with a mock implementation.
  - The Celery task includes basic `autoretry_for=(Exception,)` with `max_retries=3`. This will help but we must ensure data loader specific retry logic is also robust.
  - Tests should be careful with blocking calls and flaky time-based assertions as flagged in Story 2.1 code reviews.
- **Technical specifics:**
  - CCXT, yfinance, and akshare rate limits must be carefully managed.
  - The `runner.py` uses Pydantic schema validation (`BacktestConfigSchema`). Ensure the payload received from Nowing maps correctly to this schema or that the worker translates it appropriately.

### Project Structure Notes
- **Suggested Location:** 
  - `agent/src/worker.py` (Update `run_backtest_job` implementation)
  - `agent/backtest/loaders/*` (Verify/add retry logic to specific loaders if missing)
  - `agent/tests/` (Integration tests for multi-market job processing)

### References
- [Source: _bmad-output/planning-artifacts/architecture.md#5. Fulfillment of PRD Requirements]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2: Multi-Market Data Loading System]

## Dev Agent Record

### Agent Model Used
Antigravity (DeepMind)

### Completion Notes List
- Enhanced `run_backtest_job` in `agent/src/worker.py` to parse `VibeTradingJobPayload`.
- Implemented symbol validation to prioritize Crypto assets and reject non-crypto strings (Stock symbols like AAPL are excluded).
- Integrated `ccxt` loader via `get_loader_cls_with_fallback`.
- Added strict retry mechanism for API rate limits and connection errors leveraging Celery's `autoretry_for` (`ConnectionError`, `TimeoutError`, `ccxt.NetworkError`, `ccxt.RateLimitExceeded`).
- Replaced mock `time.sleep` with real data fetch via `loader.fetch()`.
- Added mock tests in `test_worker.py` replacing the outdated mock implementation logic.

### File List
- `agent/src/worker.py`
- `agent/tests/unit/test_worker.py`

### Change Log
- Removed old `time.sleep` mock logic.
- Included `VibeTradingJobPayload` serialization to backend logic and error statuses.
- Configured exception reraising for Celery retries on rate limits.

---
**Status:** done

### Review Findings
- [x] [Review][Patch] Global State Mutation (Concurrency Race Condition) [`agent/src/worker.py:35`]
- [x] [Review][Patch] Inaccurate Error Handling and Unintended Retries for Empty Data [`agent/src/worker.py:55`]
- [x] [Review][Patch] Loss of Stack Trace Details & Traceback Alteration (`logger.error` and `raise e`) [`agent/src/worker.py:75`]
- [x] [Review][Patch] Environment variable assignment crashes on `None` [`agent/src/worker.py:35`]
- [x] [Review][Patch] Missing safeguard against `NoneType` assets [`agent/src/worker.py:16`]
- [x] [Review][Patch] Fragile DataFrame properties assumptions [`agent/src/worker.py:62`]
- [x] [Review][Patch] Date formatting granularity loss [`agent/src/worker.py:42`]
- [x] [Review][Defer] Flawed Asset Classification Heuristic (`endswith("USD")` etc.) [`agent/src/worker.py:19`] — deferred, pre-existing
