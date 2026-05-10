import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from agent.api_server import app
import agent.api_server as api_server

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api_server, "_is_ip_whitelisted", lambda r: True)
    monkeypatch.setattr(api_server, "_API_KEY", "")
    return TestClient(app)

@patch("src.worker.run_backtest_job.apply_async")
def test_async_job_enqueue(mock_apply_async, client):
    # Mock the Celery AsyncResult
    mock_task = MagicMock()
    mock_task.id = "test-celery-task-id-1234"
    mock_apply_async.return_value = mock_task
    
    payload = {
        "simulation_environment": {
            "initial_capital": "15000",
            "historical_range": 365
        },
        "risk_management": {
            "max_drawdown_percentage": "0.15",
            "position_sizing": "0.2"
        },
        "context_rules": {
            "assets": ["BTC-USDT"],
            "timeframe": "1h"
        },
        "execution_flags": {}
    }
    
    response = client.post("/jobs", json=payload)
    
    # Assert successful response and job_id mapping
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["job_id"] == "test-celery-task-id-1234"
    
    # Assert Celery task was called with correct payload and queue
    mock_apply_async.assert_called_once()
    kwargs = mock_apply_async.call_args.kwargs
    assert kwargs.get("queue") == "backtest"
    args = mock_apply_async.call_args.kwargs.get("args")
    assert isinstance(args, list)
    assert args[0]["simulation_environment"]["initial_capital"] == "15000"
