---
story_id: '2.5'
story_key: '2-5-defi-native-simulation-environment'
epic_num: 2
story_num: 5
title: 'DeFi-Native Simulation Environment'
status: 'done'
---

# Story 2.5: DeFi-Native Simulation Environment

## User Story
**As a** Crypto/DeFi Trader,
**I want** the backtest engine to simulate on-chain conditions including Gas Fees, AMM slippage, and Impermanent Loss,
**So that** my crypto strategies (especially LP strategies) have realistic performance metrics.

## Acceptance Criteria
1. **Given** a backtest job targeting DEXes (`exchange = 'UNISWAP_V3'`)
   **When** the simulation executes trades
   **Then** it deducts dynamic Gas Fees based on the `gas_fee_model`
2. **Given** a backtest job targeting DEXes
   **When** trades are executed
   **Then** it calculates slippage dynamically based on pool liquidity depth rather than a static percentage
3. **Given** a strategy involving providing liquidity
   **When** performance metrics are evaluated
   **Then** it tracks and reports Impermanent Loss

## Tasks / Subtasks
- [x] Task 1: Implement Dynamic Gas Fee Model
  - [x] Subtask 1.1: Create a generic Gas Fee model that takes into account transaction complexity and base chain fees.
  - [x] Subtask 1.2: Integrate the gas fee deduction into the simulation engine's trade execution path.
- [x] Task 2: Implement Dynamic Slippage Model
  - [x] Subtask 2.1: Create a slippage model based on AMM pool liquidity depth (e.g. constant product formula or concentrated liquidity approximations).
  - [x] Subtask 2.2: Apply dynamic slippage to trade execution prices.
- [x] Task 3: Implement Impermanent Loss Tracking
  - [x] Subtask 3.1: Add mechanisms to track liquidity provision states.
  - [x] Subtask 3.2: Calculate and deduct Impermanent Loss based on price divergence over time.
- [x] Task 4: Integration and Testing
  - [x] Subtask 4.1: Integrate these DeFi models into the main `worker.py` execution flow when the payload indicates a DEX environment.
  - [x] Subtask 4.2: Write comprehensive unit tests for Gas, Slippage, and Impermanent Loss calculations.

## Dev Notes

### 🏗️ Architecture & Guardrails
- **Payload Constraints**: Ensure `gas_fee_model`, `track_impermanent_loss`, and `slippage_tolerance` from the `SimulationEnvironment` in `VibeTradingJobPayload` are properly utilized.
- **Execution Environment**: This feature focuses purely on Crypto-native mechanics (Epic 2 Phase 1) and must be isolated from traditional stock market logic.
- **Mathematical Precision**: Use `Decimal` types or `float64` for all financial math (Impermanent Loss and Slippage) to prevent float drift.
- **Performance**: Ensure that calculating dynamic slippage and IL does not bottleneck the backtest engine (aim for <30s execution for a 2-year lookback).

### 🔍 Technical Specifics
- **Impermanent Loss Formula**: Can be modeled using the standard formula for constant product AMMs: $IL = 2 \cdot \frac{\sqrt{P_{ratio}}}{1 + P_{ratio}} - 1$ where $P_{ratio}$ is the price change ratio. For Uniswap V3 concentrated liquidity, the IL calculation is more complex and depends on the price range; start with a generalized approximation or standard formula unless specifically requested otherwise.
- **Dynamic Slippage**: For constant product AMMs ($x \cdot y = k$), slippage is a function of trade size relative to pool liquidity. Model this appropriately.
- **Gas Fees**: Can be simulated as a fixed base cost + variable cost based on network congestion or just a constant model passed via `gas_fee_model`.

### 🔄 Previous Story Intelligence (from 2.4)
- **Modularity**: Like the Monte Carlo implementation, consider placing the DeFi simulation models in a dedicated module (e.g., `defi_simulator.py`) to keep `worker.py` clean.
- **Error Handling**: Remember to add proper guards for edge cases (e.g., empty data, zero liquidity) as identified in Story 2.4 code reviews.

### Project Structure Notes
- **Suggested Locations**:
  - `agent/src/defi_simulator.py` (New file for DeFi math models)
  - `agent/src/worker.py` (Integration point)
  - `agent/tests/unit/test_defi_simulator.py` (New unit tests)

### References
- [Source: _bmad-output/planning-artifacts/architecture.md]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5: DeFi-Native Simulation Environment]

## Dev Agent Record

### Agent Model Used
Antigravity (DeepMind)

### Completion Notes List
- Created `agent/src/defi_simulator.py` with mathematical models for Gas Fees, Dynamic Slippage ($x \cdot y = k$), and Impermanent Loss.
- Integrated the `DeFiSimulator` into the background worker's simulation loop.
- Implemented proxy calculations for pool liquidity and price divergence to enable realistic DEX simulation during Monte Carlo runs.
- Added comprehensive unit tests in `agent/tests/unit/test_defi_simulator.py` covering all DeFi math scenarios.
- Verified 100% test pass rate for the new simulator.

### File List
- `agent/src/defi_simulator.py`
- `agent/src/worker.py`
- `agent/tests/unit/test_defi_simulator.py`

### Change Log
- Added DeFi-specific simulation logic to penalize DEX strategy returns based on on-chain conditions.
- Updated worker to detect DEX environments and instantiate the appropriate simulator.

---
**Status:** done
