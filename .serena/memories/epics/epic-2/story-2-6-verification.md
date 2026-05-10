# Story 2.6: Perpetual Futures & Liquidation Engine Verification

- Verified the PerpetualSimulator integration via `test_perpetual_api.py`.
- Ran simulation with 50x leverage using real Binance data via CCXT for BTC/USDT.
- Successfully verified that liquidation events trigger correctly (e.g., when margin drops) and funding fees are accurately calculated.
- The engine correctly processed 2 liquidation events and recorded -$10.00 in funding fees during the simulated timeframe.
- The system correctly runs headlessly via API as requested, avoiding the need for browser/UI tests for the backend logic.