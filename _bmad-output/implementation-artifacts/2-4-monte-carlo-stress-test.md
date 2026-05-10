# Story 2.4: Monte Carlo Stress Test

## Story Foundation
**Story ID:** 2.4
**Epic:** Epic 2: Crypto-Native Async Execution Engine (Phase 1)
**Title:** Monte Carlo Stress Test

**User Story:**
As a Risk-Averse Trader,
I want the engine to run Monte Carlo simulations (resampling) on my backtest results,
So that I can see the probability of "Black Swan" events and extreme drawdowns.

**Acceptance Criteria:**
- **Given** a successfully completed backtest job with `enable_monte_carlo_stress_test=true`
- **When** the worker processes the flag
- **Then** it runs 10,000+ resampled paths on the historical trade series
- **And** it outputs a risk distribution graph and 95% Confidence Interval metrics

## Developer Context

### Technical Requirements
- **Integration Point**: The Monte Carlo logic needs to run *after* the backtest is successfully completed and the historical trade series is available.
- **Trigger**: Check the `enable_monte_carlo_stress_test` flag inside the `VibeTradingJobPayload` -> `execution_flags` or `simulation_environment` (verify schema).
- **Implementation Mechanism**: Use `numpy` or `pandas` to randomly resample the trade returns (with replacement) 10,000 times to create 10,000 equity curves.
- **Metrics Calculation**: From the 10,000 equity curves, calculate:
  - Worst-case Max Drawdown at 95% Confidence Interval (95% CI).
  - Risk of Ruin probability.
  - Final Capital distribution (Mean, Median, 5th percentile, 95th percentile).
- **Persistence**: Save the Monte Carlo metrics inside `metadata.json` (or a dedicated `monte_carlo_metrics.json`), and potentially save a summarized path data or histogram representation for the "risk distribution graph". Since storing 10,000 paths as CSV might be too large, compute the histogram/percentile curves and save those instead.

### Architecture Compliance
- **Worker Isolation**: The Monte Carlo stress test is computationally intensive. It should be handled by the worker seamlessly, but ensure `numpy` operations are vectorized to prevent the job from exceeding timeout limits.
- **Data Types**: Ensure Decimal or at least `float64` is used to prevent float drift during the 10k cumulative product calculations.

### Library & Framework Requirements
- **Numpy/Pandas**: Use `np.random.choice` for resampling. Ensure vectorization instead of loops for 10,000 iterations to meet performance requirements.
- **Shared Persistence**: The output files must be saved to the same `/runs/<job_id>` directory established in Story 2.3.

### File Structure Requirements
- `agent/src/worker.py`: Update the worker logic to detect the flag and invoke the Monte Carlo processor.
- Create a new module (e.g., `agent/src/monte_carlo.py` or similar) to house the simulation logic to keep `worker.py` clean.
- Ensure the result schema is structured well.

### Testing Requirements
- Unit tests verifying the Monte Carlo engine handles an empty trade list safely.
- Unit tests validating the mathematical accuracy of the 95% CI and percentiles.
- Integration tests ensuring the worker properly saves the results when the flag is true, and skips it when false.

## Previous Story Intelligence
- Story 2.3 introduced the `runs/<job_id>` persistent storage layer. Leverage the same directory pattern for outputting the Monte Carlo results. The `VibeTradingJobPayload` has been defined; make sure to add `enable_monte_carlo_stress_test` if it doesn't already exist or check where it's parsed.

## Project Context Reference
- **Project**: Vibe-Trading Integration (Nowing)
- **Role**: Vibe-Trading is the Execution Engine (Stateless-ish). Nowing is the Source of Truth.
- **Persistence**: Shared File System inside `runs/`.

## Completion Status
**Status:** ready-for-dev
