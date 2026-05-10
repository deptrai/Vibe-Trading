import sys
from unittest.mock import MagicMock
import pandas as pd

class DummyCelery:
    def __init__(self, *args, **kwargs):
        self.conf = MagicMock()
    def task(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

mock_celery = MagicMock()
mock_celery.Celery = DummyCelery
sys.modules["celery"] = mock_celery

import pytest
from src.worker import run_backtest_job

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
    assert result["payload_received"] == sample_payload
    
    # Check if files were created
    job_dir = tmp_path / "test_job_id"
    assert job_dir.exists()
    assert (job_dir / "BTC_USDT.csv").exists()
    assert (job_dir / "metadata.json").exists()

def test_run_backtest_job_2_year_constraint(monkeypatch, sample_payload, tmp_path):
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    sample_payload["simulation_environment"]["historical_range"] = 1000  # More than 2 years
    
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    
    df = pd.DataFrame({"close": [1, 2]}, index=pd.date_range("2024-01-01", periods=2))
    mock_loader.fetch.return_value = {"BTC-USDT": df}
    mock_loader_cls.return_value = mock_loader
    monkeypatch.setattr("backtest.loaders.registry.get_loader_cls_with_fallback", lambda x: mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_constraint"
    
    result = run_backtest_job(mock_self, sample_payload)
    
    # Verify fetch was called with a constrained date (approx 730 days diff)
    call_kwargs = mock_loader.fetch.call_args[1]
    from datetime import datetime, timezone
    start_date = datetime.fromisoformat(call_kwargs["start_date"]).replace(tzinfo=timezone.utc)
    end_date = datetime.fromisoformat(call_kwargs["end_date"]).replace(tzinfo=timezone.utc)
    diff_days = (end_date - start_date).days
    assert diff_days == 730
    
    # Check metadata reflects the constraint
    import json
    metadata_path = tmp_path / "test_job_constraint" / "metadata.json"
    assert metadata_path.exists()
    with open(metadata_path, "r") as f:
        meta = json.load(f)
        assert meta["requested_range_days"] == 1000
        assert meta["effective_range_days"] == 730

def test_run_backtest_job_no_crypto_assets(monkeypatch, sample_payload):
    sample_payload["context_rules"]["assets"] = ["AAPL", "GOOG"]
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    
    result = run_backtest_job(mock_self, sample_payload)
    
    assert result["status"] == "error"
    assert "No valid crypto assets" in result["message"]

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
    data_summary = result["data_summary"]["BTC-USDT"]
    
    assert "monte_carlo" in data_summary
    mc_results = data_summary["monte_carlo"]
    assert mc_results["iterations"] == 10000
    assert "metrics" in mc_results
    assert "final_capital" in mc_results["metrics"]
    assert "mean" in mc_results["metrics"]["final_capital"]
    
    # Check if the JSON file was created
    mc_json_path = tmp_path / "mc_test_job_id" / "BTC_USDT_monte_carlo.json"
    assert mc_json_path.exists()
