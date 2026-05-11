from __future__ import annotations
import pytest
import jwt
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

@pytest.fixture
def mock_run_backtest_job():
    with patch("src.worker.run_backtest_job.apply_async") as mock_apply:
        mock_task = MagicMock()
        mock_task.id = "mock_task_id"
        mock_apply.return_value = mock_task
        yield mock_apply

@pytest.fixture
def mock_run_rl_job():
    with patch("src.rl_worker.run_rl_optimization_job.apply_async") as mock_apply:
        mock_task = MagicMock()
        mock_task.id = "mock_rl_task_id"
        mock_apply.return_value = mock_task
        yield mock_apply

@pytest.fixture
def payload():
    return {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": "10000.0"
        },
        "risk_management": {
            "max_drawdown_percentage": "0.2",
            "position_sizing": "0.1",
            "leverage": "1.0"
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1h",
            "executable_code": "pass"
        },
        "execution_flags": {
            "enable_rl_optimization": False,
            "rl_max_trials": 50,
            "rl_optimization_target": "sharpe"
        }
    }

def test_create_job_missing_jwt(mock_run_backtest_job, payload):
    # No Auth header
    response = client.post("/jobs", json=payload)
    # Since require_auth depends on API_AUTH_KEY or IP whitelist, 
    # if we are hitting localhost with TestClient, it is whitelisted.
    # We should get accepted and routed to standard.
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    mock_run_backtest_job.assert_called_once()
    assert mock_run_backtest_job.call_args[1]["queue"] == "backtest.standard"

def test_create_job_invalid_jwt(mock_run_backtest_job, payload, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "supersecret")
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = client.post("/jobs", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    mock_run_backtest_job.assert_called_once()
    assert mock_run_backtest_job.call_args[1]["queue"] == "backtest.standard"

def test_create_job_valid_premium_jwt(mock_run_backtest_job, payload, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "supersecret")
    token = jwt.encode({"user_tier": "premium"}, "supersecret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/jobs", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    mock_run_backtest_job.assert_called_once()
    assert mock_run_backtest_job.call_args[1]["queue"] == "backtest.premium"

def test_create_job_valid_standard_jwt(mock_run_backtest_job, payload, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "supersecret")
    token = jwt.encode({"user_tier": "standard"}, "supersecret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/jobs", json=payload, headers=headers)
    assert response.status_code == 200
    mock_run_backtest_job.assert_called_once()
    assert mock_run_backtest_job.call_args[1]["queue"] == "backtest.standard"

def test_create_rl_job_premium(mock_run_rl_job, payload, monkeypatch):
    payload["execution_flags"]["enable_rl_optimization"] = True
    monkeypatch.setenv("JWT_SECRET", "supersecret")
    token = jwt.encode({"user_tier": "premium"}, "supersecret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/jobs", json=payload, headers=headers)
    assert response.status_code == 200
    mock_run_rl_job.assert_called_once()
    assert mock_run_rl_job.call_args[1]["queue"] == "rl_optimization.premium"
