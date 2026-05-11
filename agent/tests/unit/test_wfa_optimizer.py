import os
import json
import pytest
import pandas as pd
import numpy as np
from src.rl_optimizer import RLOptimizer
from unittest.mock import MagicMock

class MockWFAConfig:
    def __init__(self, is_p=5, oos_p=1, step=1):
        self.in_sample_periods = is_p
        self.out_of_sample_periods = oos_p
        self.step_size = step

@pytest.fixture
def mock_market_data():
    dates = pd.date_range(start="2020-01-01", periods=500, freq="D")
    data = pd.DataFrame({
        "close": np.random.randn(500).cumsum() + 100
    }, index=dates)
    return {"BTC/USDT": data}

@pytest.fixture
def optimizer(tmp_path):
    job_dir = tmp_path / "wfa_run"
    job_dir.mkdir()
    # Mocking objective to return fixed scores for deterministic tests
    opt = RLOptimizer(job_dir=str(job_dir), target="sharpe", max_trials=5)
    return opt

def test_wfa_window_generation(optimizer, mock_market_data):
    wfa_config = MockWFAConfig(is_p=7, oos_p=3, step=1)
    # Total points = 500. window_size = 500 // 4 = 125. 
    # Ratio = 7:3 -> IS = 125 * 0.7 = 87, OOS = 38.
    
    # We use a mocked optimize to avoid slow optuna trials
    optimizer.optimize = MagicMock(return_value={
        "status": "completed", 
        "best_score": 1.0, 
        "best_params": {"rsi": 10}
    })
    
    # Mock _simulate_backtest to avoid complexity
    optimizer._simulate_backtest = MagicMock(return_value=1.5)
    
    result = optimizer.walk_forward_optimize(mock_market_data, wfa_config)
    
    assert result["status"] == "completed"
    assert "wfa" in result
    windows = result["wfa"]["windows"]
    
    # With overlapping windows and step_size logic, we should have around 10-20 windows
    assert len(windows) >= 3
    
    # Verify first window ranges
    first = windows[0]
    assert "is_range" in first
    assert "oos_range" in first
    assert first["is_score"] == 1.0
    assert first["oos_score"] == 1.5

def test_wfa_aggregation_logic(optimizer, mock_market_data):
    wfa_config = MockWFAConfig()
    
    # Return different scores for each window. Provide many items to avoid StopIteration.
    scores = [float(i) for i in range(1, 31)]
    optimizer.optimize = MagicMock()
    optimizer.optimize.side_effect = [{"status": "completed", "best_score": s, "best_params": {}} for s in scores]
    
    # OOS scores half of IS
    optimizer._simulate_backtest = MagicMock()
    optimizer._simulate_backtest.side_effect = [s/2.0 for s in scores]
    
    result = optimizer.walk_forward_optimize(mock_market_data, wfa_config)
    
    wfa = result["wfa"]
    num_windows = len(wfa["windows"])
    assert num_windows >= 3
    
    expected_is_mean = np.mean(scores[:num_windows])
    assert pytest.approx(wfa["is_mean_score"], 0.001) == expected_is_mean
    
    expected_oos_mean = np.mean([s/2.0 for s in scores[:num_windows]])
    assert pytest.approx(wfa["oos_mean_score"], 0.001) == expected_oos_mean
    assert pytest.approx(float(wfa["decay_rate"]), 0.001) == -0.5

def test_wfa_insufficient_data(optimizer):
    # Only 10 points
    dates = pd.date_range(start="2020-01-01", periods=10, freq="D")
    data = pd.DataFrame({"close": range(10)}, index=dates)
    market_data = {"BTC": data}
    
    wfa_config = MockWFAConfig()
    result = optimizer.walk_forward_optimize(market_data, wfa_config)
    
    assert result["status"] == "error"
    assert "Insufficient overlapping data" in result["message"]

def test_wfa_persistence(optimizer, mock_market_data):
    wfa_config = MockWFAConfig()
    optimizer.optimize = MagicMock(return_value={"status": "completed", "best_score": 1.0, "best_params": {"rsi": 10}, "total_trials": 5, "trial_history": [], "elapsed_seconds": 1})
    optimizer._simulate_backtest = MagicMock(return_value=1.2)
    
    optimizer.walk_forward_optimize(mock_market_data, wfa_config)
    
    out_path = os.path.join(optimizer.job_dir, "optimized_params.json")
    assert os.path.exists(out_path)
    
    with open(out_path, "r") as f:
        data = json.load(f)
        assert "wfa" in data
        assert data["wfa"]["decay_rate"] > 0
