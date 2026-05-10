# DeFi Simulator Module

Added `DeFiSimulator` to `agent/src/defi_simulator.py` to handle crypto-native simulation conditions.
- **Gas Fees**: Implemented customizable gas fee model (`low`, `default`, `high`) based on base fee and multiplier.
- **Dynamic Slippage**: Integrated x*y=k constant product approximation ($impact \approx \frac{tradeSize}{liquidity}$) and added a strict cap at 10% to prevent excessive loss on low liquidity calculations.
- **Impermanent Loss**: Tracked LP positions (price/amount) and used standard AMM formula: `IL = 2 * sqrt(P_ratio) / (1 + P_ratio) - 1` with math.sqrt and Decimal processing.
- **Integration**: Refactored `agent/src/worker.py` within `run_backtest_job` to instantiate `DeFiSimulator` when `job_payload.simulation_environment.exchange` explicitly points to a DEX exchange (e.g. uniswap, sushiswap, curve). Modified mock simulated trade returns to deduct dynamic fees.
- **Precision**: Used `Decimal` extensively for exact financial math, preventing float drift.
- **Tests**: Covered thoroughly via `agent/tests/unit/test_defi_simulator.py`.