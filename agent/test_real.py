import sys
import os

# Ensure src module can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.worker import run_backtest_job
from unittest.mock import MagicMock

def test_real_data():
    payload = {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": 10000.0,
            "trading_fees": 0.001,
            "slippage_tolerance": 0.001,
            "historical_range": 1000  # requesting 1000 days, should be capped at 730
        },
        "risk_management": {
            "max_drawdown_percentage": 0.2,
            "position_sizing": 0.1,
            "leverage": 1.0
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1d"
        },
        "execution_flags": {
            "enable_monte_carlo_stress_test": False,
            "enable_rl_optimization": False
        }
    }
    
    mock_self = MagicMock()
    mock_self.request.id = "test_real_job_123"
    
    print("Running job...")
    try:
        # Patch the real request.id temporarily
        run_backtest_job.request.id = "test_real_job_123"
        result = run_backtest_job(payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return
    
    print("Result:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_real_data()
