import pytest
from unittest.mock import MagicMock
import pandas as pd
from datetime import datetime, timezone
import json
from src.worker import run_backtest_job as worker_task

# Extract the UNBOUND raw function to bypass Celery's decorator and binding logic
run_backtest_job = worker_task.__wrapped__.__func__ if hasattr(worker_task.__wrapped__, "__func__") else worker_task.__wrapped__

@pytest.fixture
def sample_payload():
    return {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": 10000.0,
            "trading_fees": 0.001,
            "slippage_tolerance": 0.001,
            "historical_range": 30
        },
        "risk_management": {
            "max_drawdown_percentage": 0.2,
            "position_sizing": 0.1,
            "leverage": 1.0
        },
        "context_rules": {
            "assets": ["BTC-USDT", "AAPL"],
            "timeframe": "1h"
        },
        "execution_flags": {
            "enable_monte_carlo_stress_test": False,
            "enable_rl_optimization": False
        }
    }

def test_run_backtest_job_success(monkeypatch, sample_payload, tmp_path):
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    
    df = pd.DataFrame({"close": [1, 2, 3]}, index=pd.date_range("2024-01-01", periods=3))
    mock_loader.fetch.return_value = {"BTC-USDT": df}
    mock_loader_cls.return_value = mock_loader
    
    monkeypatch.setattr("backtest.loaders.registry.get_loader_cls_with_fallback", lambda x: mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    
    result = run_backtest_job(mock_self, sample_payload)
    
    assert result["status"] == "success"
    assert result["job_id"] == "test_job_id"
    assert "BTC-USDT" in result["data_summary"]
    assert "AAPL" in result["rejected_assets"]

def test_run_backtest_job_2_year_constraint(monkeypatch, sample_payload, tmp_path):
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    sample_payload["simulation_environment"]["historical_range"] = 1000
    
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    
    df = pd.DataFrame({"close": [1, 2]}, index=pd.date_range("2024-01-01", periods=2))
    mock_loader.fetch.return_value = {"BTC-USDT": df}
    mock_loader_cls.return_value = mock_loader
    monkeypatch.setattr("backtest.loaders.registry.get_loader_cls_with_fallback", lambda x: mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_constraint"
    
    result = run_backtest_job(mock_self, sample_payload)
    
    call_kwargs = mock_loader.fetch.call_args[1]
    start_date = datetime.fromisoformat(call_kwargs["start_date"]).replace(tzinfo=timezone.utc)
    end_date = datetime.fromisoformat(call_kwargs["end_date"]).replace(tzinfo=timezone.utc)
    diff_days = (end_date - start_date).days
    assert 728 <= diff_days <= 732
    
def test_run_backtest_job_no_crypto_assets(monkeypatch, sample_payload):
    sample_payload["context_rules"]["assets"] = ["AAPL", "GOOG"]
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    result = run_backtest_job(mock_self, sample_payload)
    assert result["status"] == "error"

def test_run_backtest_job_fetch_fails(monkeypatch, sample_payload):
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    mock_loader.fetch.side_effect = ConnectionError("Mocked fetch error")
    mock_loader_cls.return_value = mock_loader
    monkeypatch.setattr("backtest.loaders.registry.get_loader_cls_with_fallback", lambda x: mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    with pytest.raises(ConnectionError):
        run_backtest_job(mock_self, sample_payload)

def test_run_backtest_job_monte_carlo(monkeypatch, sample_payload, tmp_path):
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    sample_payload["execution_flags"]["enable_monte_carlo_stress_test"] = True
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    df = pd.DataFrame({"close": [100.0, 105.0, 95.0, 110.0]}, index=pd.date_range("2026-05-01", periods=4))
    mock_loader.fetch.return_value = {"BTC-USDT": df}
    mock_loader_cls.return_value = mock_loader
    monkeypatch.setattr("backtest.loaders.registry.get_loader_cls_with_fallback", lambda x: mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "mc_test_job_id"
    result = run_backtest_job(mock_self, sample_payload)
    assert result["status"] == "success"

def test_run_backtest_job_perpetual_high_leverage(monkeypatch, sample_payload, tmp_path):
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    sample_payload["execution_flags"]["enable_monte_carlo_stress_test"] = True
    sample_payload["simulation_environment"]["instrument_type"] = "PERPETUAL"
    sample_payload["risk_management"]["leverage"] = 100.0
    
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    df = pd.DataFrame({"close": [100.0, 101.0, 95.0, 110.0]}, index=pd.date_range("2026-05-01", periods=4))
    mock_loader.fetch.return_value = {"BTC-USDT": df}
    mock_loader_cls.return_value = mock_loader
    monkeypatch.setattr("backtest.loaders.registry.get_loader_cls_with_fallback", lambda x: mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "mc_perp_test_job_id"
    result = run_backtest_job(mock_self, sample_payload)
    
    assert result["status"] == "success"
    
    import os
    import json
    mc_path = os.path.join(str(tmp_path), "mc_perp_test_job_id", "BTC_USDT_monte_carlo.json")
    with open(mc_path, "r") as f:
        mc_data = json.load(f)
    assert "liquidation_events" in mc_data
    assert "total_funding_fees" in mc_data
