import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from decimal import Decimal
from src.rl_optimizer import RLOptimizer

@pytest.fixture
def dummy_market_data():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 100)) * 100
    df = pd.DataFrame({"close": prices}, index=dates)
    return {"BTC/USDT": df}

def test_rl_optimizer_schema(dummy_market_data):
    with tempfile.TemporaryDirectory() as tmp_dir:
        optimizer = RLOptimizer(job_dir=tmp_dir, target="sharpe", max_trials=5)
        result = optimizer.optimize(market_data=dummy_market_data)
        
        assert result["status"] == "completed"
        assert "best_params" in result
        assert "best_score" in result
        assert result["total_trials"] == 5
        assert len(result["trial_history"]) == 5
        assert result["optimization_target"] == "sharpe"
        
        # Check progress file
        progress_file = os.path.join(tmp_dir, "progress.json")
        assert os.path.exists(progress_file)
        with open(progress_file) as f:
            prog = json.load(f)
            assert prog["current_trial"] == 5
            assert prog["total_trials"] == 5

def test_rl_optimizer_sharpe_calculation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        optimizer = RLOptimizer(job_dir=tmp_dir, target="sharpe", max_trials=1)
        
        # A perfectly linear trend will yield a specific Sharpe
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        df = pd.DataFrame({"close": np.linspace(100, 200, 100)}, index=dates)
        
        params = {
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "ma_period": 50,
            "stop_loss_pct": 0.0,  # Zero noise for stable test
            "take_profit_pct": 0.1
        }
        
        score = optimizer._simulate_backtest(params, {"TEST": df})
        assert isinstance(score, Decimal)
        assert float(score) > 0

def test_rl_optimizer_parameter_bounds():
    with tempfile.TemporaryDirectory() as tmp_dir:
        optimizer = RLOptimizer(job_dir=tmp_dir, target="pnl", max_trials=10)
        
        # Empty df
        empty_data = {"BTC/USDT": pd.DataFrame()}
        result = optimizer.optimize(market_data=empty_data)
        
        # Best score should be 0 since no returns
        assert result["best_score"] == 0.0
        
        # Check trial params are within bounds
        for trial in result["trial_history"]:
            p = trial["params"]
            assert 5 <= p["rsi_period"] <= 30
            assert 0.01 <= p["stop_loss_pct"] <= 0.10
