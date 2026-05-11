import pytest
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Import the worker function
from src.worker import run_backtest_job


@patch('src.worker.subprocess.run')
def test_direct_execution_bypass_llm(mock_subprocess_run, tmp_path, monkeypatch):
    """E2E: executable_code path writes signal_engine.py and runs backtest.runner"""
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))

    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    # Create mock market data
    dates = pd.date_range("2024-01-01", periods=100, freq="1h")
    mock_df = pd.DataFrame({
        "open": np.random.uniform(40000, 45000, 100),
        "high": np.random.uniform(40000, 45000, 100),
        "low": np.random.uniform(40000, 45000, 100),
        "close": np.random.uniform(40000, 45000, 100),
        "volume": np.random.uniform(100, 1000, 100),
    }, index=dates)

    mock_loader = MagicMock()
    mock_loader.fetch.return_value = {"BTC/USDT": mock_df}

    payload = {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": "10000.0",
            "historical_range": 30
        },
        "risk_management": {
            "leverage": "1.0",
            "position_sizing": "0.1",
            "max_drawdown_percentage": "0.2"
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1h",
            "executable_code": "def next(self): pass"
        },
        "execution_flags": {
            "enable_monte_carlo_stress_test": False,
            "enable_rl_optimization": False,
            "rl_max_trials": 50,
            "rl_optimization_target": "sharpe"
        }
    }

    # Mock task request via Celery Task
    mock_request = MagicMock()
    mock_request.id = "test-job-id"

    # Pre-create mock artifacts so the worker picks them up
    job_dir = tmp_path / "test-job-id"
    artifacts_dir = job_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "equity.csv").write_text("mock equity data")
    (artifacts_dir / "metrics.csv").write_text("mock metrics data")

    with patch('celery.app.task.Task.request', new_callable=unittest.mock.PropertyMock, return_value=mock_request), \
         patch('backtest.loaders.registry.get_loader_cls_with_fallback', return_value=lambda: mock_loader):
        result = run_backtest_job(payload)

    assert result["status"] == "success"
    assert result["job_id"] == "test-job-id"
    assert "artifacts" in result
    assert "equity.csv" in result["artifacts"]
    assert "metrics.csv" in result["artifacts"]

    # Worker writes signal_engine.py (not strategy.py)
    strategy_file = job_dir / "code" / "signal_engine.py"
    assert strategy_file.exists()

    with open(strategy_file, "r") as f:
        content = f.read()
    assert content == "def next(self): pass"


@patch('src.worker.subprocess.run')
@patch('src.agent.loop.AgentLoop.run_headless')
def test_natural_language_generation(mock_run_headless, mock_subprocess_run, tmp_path, monkeypatch):
    """E2E: natural_language_rules path invokes AgentLoop.run_headless then backtest.runner"""
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))

    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    mock_run_headless.return_value = {"status": "success", "run_dir": str(tmp_path / "test-job-id")}

    # Create mock market data
    dates = pd.date_range("2024-01-01", periods=100, freq="1h")
    mock_df = pd.DataFrame({
        "open": np.random.uniform(40000, 45000, 100),
        "high": np.random.uniform(40000, 45000, 100),
        "low": np.random.uniform(40000, 45000, 100),
        "close": np.random.uniform(40000, 45000, 100),
        "volume": np.random.uniform(100, 1000, 100),
    }, index=dates)

    mock_loader = MagicMock()
    mock_loader.fetch.return_value = {"BTC/USDT": mock_df}

    payload = {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": "10000.0",
            "historical_range": 30
        },
        "risk_management": {
            "leverage": "1.0",
            "position_sizing": "0.1",
            "max_drawdown_percentage": "0.2"
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1h",
            "natural_language_rules": "Buy when RSI < 30"
        },
        "execution_flags": {
            "enable_monte_carlo_stress_test": False,
            "enable_rl_optimization": False,
            "rl_max_trials": 50,
            "rl_optimization_target": "sharpe"
        }
    }

    # Mock task request via Celery Task
    mock_request = MagicMock()
    mock_request.id = "test-job-id"

    # Pre-create mock artifacts so the worker picks them up
    job_dir = tmp_path / "test-job-id"
    artifacts_dir = job_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "equity.csv").write_text("mock equity data")
    (artifacts_dir / "metrics.csv").write_text("mock metrics data")

    with patch('celery.app.task.Task.request', new_callable=unittest.mock.PropertyMock, return_value=mock_request), \
         patch('backtest.loaders.registry.get_loader_cls_with_fallback', return_value=lambda: mock_loader):
        result = run_backtest_job(payload)

    assert result["status"] == "success"
    assert result["job_id"] == "test-job-id"
    assert "artifacts" in result
    assert "equity.csv" in result["artifacts"]
    assert "metrics.csv" in result["artifacts"]

    mock_run_headless.assert_called_once()
