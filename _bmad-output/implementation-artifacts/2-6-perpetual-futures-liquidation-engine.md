---
story_id: '2.6'
story_key: '2-6-perpetual-futures-liquidation-engine'
epic_num: 2
story_num: 6
title: 'Perpetual Futures & Liquidation Engine'
status: 'done'
---

# Story 2.6: Perpetual Futures & Liquidation Engine

## User Story
**As a** Derivatives Trader,
**I want** the backtest engine to simulate Perpetual Futures mechanics including Funding Rates and Margin Liquidations,
**So that** I can accurately backtest high-leverage strategies and understand my risk of liquidation.

## Acceptance Criteria
1. **Given** a backtest job trading Perpetual Futures (`instrument_type = 'PERPETUAL'`) with leverage > 1x
   **When** the simulation executes
   **Then** it deducts/adds Funding Rate payments based on simulated 8-hour intervals.
2. **Given** a Perpetual Futures position
   **When** the price moves against the position
   **Then** it accurately triggers liquidation if the margin ratio drops below the maintenance threshold (e.g., 0.5% or 1%).
3. **Given** a backtest report
   **When** results are generated
   **Then** it includes a "Liquidation Events" log and total funding fees paid/received.

---

## Developer Context

### Technical Requirements
- **Margin Calculation:** 
  - Ensure leverage is applied to the position size: `position_size = initial_capital * leverage`.
  - Use a default maintenance margin ratio (MMR) of 1% (0.01) unless overridden by user configurations.
- **Funding Mechanics:** 
  - Simulating funding rates should track standard 8-hour intervals (00:00, 08:00, 16:00 UTC).
  - Implement `calculate_funding_fee(position_size, funding_rate)` taking into account positive/negative rates based on Long/Short positioning.
- **Liquidation Mechanics:**
  - *Liquidation Price (Long):* `P_liq = P_entry * (1 - IMR + MMR)`
  - *Liquidation Price (Short):* `P_liq = P_entry * (1 + IMR - MMR)`
  - `IMR` (Initial Margin Ratio) = `1 / leverage`.
  - Implement `check_liquidation` logic checking if the mark price crosses `P_liq`.

### Architecture Compliance
- **Stateless Execution:** Keep mathematical operations pure inside `agent/src/perpetual_simulator.py`. The state of a backtest sequence (prices, balance over time) should be driven by `agent/src/worker.py` or a dedicated loop inside it (similar to Monte Carlo execution).
- **Precision (NFR5):** Use `Decimal` from Python's standard library for ALL financial math to prevent float drift in large numbers.
- **Payload Schema Updates:** Ensure `VibeTradingJobPayload` correctly exposes `instrument_type` and `leverage` correctly via Pydantic so `worker.py` can parse it.
- **Conditionals:** Just as DeFi simulator is triggered by DEX exchange names, Perpetual futures simulation should strictly be triggered by `instrument_type == 'PERPETUAL'`.

### Library & Framework Requirements
- `pydantic`: For validating incoming leverage and margin requirements in `api_models.py`.
- `decimal`: Strictly enforce `Decimal` for all PnL and margin variables inside `PerpetualSimulator`.
- `celery`: Must run safely inside the Celery worker process without leaking state between tasks.

### File Structure Requirements
- **NEW:** `agent/src/perpetual_simulator.py` (Contains the `PerpetualSimulator` class).
- **NEW:** `agent/tests/unit/test_perpetual_simulator.py` (Unit tests for margin, liquidation, and funding).
- **UPDATE:** `agent/src/worker.py` (To instantiate `PerpetualSimulator` when `instrument_type == 'PERPETUAL'` and integrate into the main loop).
- **UPDATE:** `agent/src/api_models.py` (Ensure `instrument_type` enum handles 'PERPETUAL' and `leverage` property exists under RiskManagement).

### Testing Requirements
- **Unit Tests:** Must test boundary cases for liquidation (e.g., exact price hits `P_liq`, just above, just below).
- **Funding Interval Tests:** Ensure funding is only applied when the timestamp crosses an 8-hour UTC boundary.
- **Integration Test:** Modify or add a test mimicking a high leverage trade (e.g. 50x or 100x) that successfully simulates a liquidation event when price plummets.

---

## Previous Story Intelligence (from Story 2.5)
- **Modular Approach Works:** In Story 2.5, we successfully separated DeFi mechanics into `DeFiSimulator` which keeps `worker.py` cleaner. Apply the exact same pattern for `PerpetualSimulator`.
- **Monte Carlo Loop Check:** In the previous story, penalties were applied directly to a vectorized Pandas array for Monte Carlo. For Perpetual futures liquidation, because liquidation is path-dependent (it happens at a specific point in time and terminates the trade), simple vectorized array multiplication might not suffice. Be careful about how path dependency is handled in backtesting or Monte Carlo scenarios! If it requires an iterative loop over `asset_returns`, ensure the performance overhead is acceptable or optimized.

## Git Intelligence Summary
- Recent commits introduced `DeFiSimulator` and 2-year lookback constraints in `worker.py`. The `worker.py` is becoming a central hub. It's critical to inject `PerpetualSimulator` gracefully without turning `worker.py` into a monolith.
- `ccxt` is being used as the primary data fetcher. The data fetched will be used to simulate these liquidations.

## Latest Tech Information
- **CCXT & Funding Rates:** Note that `ccxt` can fetch historical funding rates for some exchanges (`fetch_funding_rate_history`). If it's too slow or unavailable, consider a fallback mechanism (e.g., a static mock funding rate like 0.01% for backtesting purposes to avoid failing the simulation).

## Project Context Reference
- **Tech Stack:** Python 3.11+, Pydantic v2.
- **Code Style:** Google-style docstrings, strict type hinting (`from __future__ import annotations`), `snake_case` functions.
- **Workflow:** This task touches critical simulation math. Be sure to mock out any external calls in the unit tests!

## Tasks/Subtasks

- [x] Task 1: Create `PerpetualSimulator` class with margin, funding, and liquidation logic.
  - [x] Write unit tests (`agent/tests/unit/test_perpetual_simulator.py`).
  - [x] Implement `check_liquidation` and `calculate_funding_fee` using `Decimal`.
- [x] Task 2: Integrate `PerpetualSimulator` into `worker.py`.
  - [x] Add condition for `instrument_type == 'PERPETUAL'`.
  - [x] In the simulation loop, track position margin and trigger liquidations if price drops below P_liq.
  - [x] Apply funding fees based on 8-hour intervals.
- [x] Task 3: Finalize and verify.
  - [x] Ensure all new unit and integration tests pass without regression.

## Dev Agent Record

### Implementation Plan
- Implemented `PerpetualSimulator` in `agent/src/perpetual_simulator.py`.
- Wrote math-heavy tests with `Decimal` in `test_perpetual_simulator.py`.
- Integrated simulation inside the `worker.py` Celery task.
- Fixed `test_worker.py` testing issues with `__wrapped__.__func__`.
- Added high-leverage integration test to `test_worker.py`.

### Completion Notes
All objectives achieved. `PerpetualSimulator` math is clean and uses `Decimal`. It has been integrated into the central backtest execution loop inside `worker.py`. We fixed the long-standing `test_worker.py` Celery signature issue, verifying our changes with successful integration tests.

## File List
- `agent/src/perpetual_simulator.py`
- `agent/tests/unit/test_perpetual_simulator.py`
- `agent/src/worker.py`
- `agent/tests/unit/test_worker.py`
- `agent/src/api_models.py`

## Change Log
- Added `PerpetualSimulator`.
- Hooked up `worker.py` with `PerpetualSimulator` loops, injecting funding intervals and margin checks based on price returns.
- Fixed `run_backtest_job` reference in tests to bypass `Celery` wrappers.
- Wrote specific 100x high leverage test that successfully triggers liquidation logic.

### Review Findings

#### 🚩 Decision Needed
- [x] [Review][Decision] **Post-Liquidation Strategy State** — Đã chọn giải pháp (A) Dừng hoàn toàn chiến lược sau khi thanh lý để phản ánh đúng thực tế cháy tài khoản.
- [x] [Review][Decision] **Funding Rate Source** — Đã chọn giải pháp (A) Tiếp tục dùng mock `0.0001` cho MVP để đảm bảo hiệu năng, nhưng logic đã sẵn sàng cho dữ liệu thực.

#### 🛠️ Patches
- [x] [Review][Patch] **Sub-hourly Funding Fee Multiplication** — Đã fix bằng cách tracking `last_funding_ts`.
- [x] [Review][Patch] **Non-Cumulative Liquidation Logic** — Đã cập nhật tracking stateful cho liquidation.
- [x] [Review][Patch] **Performance Bottleneck in Simulation Loop** — Đã đưa các phép tính `Decimal` ra ngoài vòng lặp.
- [x] [Review][Patch] **Mixed Types & Precision Loss** — Đã tối ưu hóa việc ép kiểu.
- [x] [Review][Patch] **Zero Initial Capital Crash Risk** — Đã thêm check `initial_cap_dec > 0`.

#### 💤 Deferred
- [x] [Review][Defer] **Brittle Test Runner Logic** — Việc dùng `__wrapped__.__func__` để bypass Celery phụ thuộc vào cấu trúc internal của thư viện. [agent/tests/unit/test_worker.py:10] — deferred, pre-existing (cần refactor kiến trúc test chung của project sau).

---
**Status:** done
**Completion Note:** Successfully implemented Perpetual Futures Engine, resolved test runner blockers, and integrated features completely.
