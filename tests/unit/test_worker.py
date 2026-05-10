import pytest
from unittest.mock import MagicMock
from src.worker import run_backtest_job

def test_run_backtest_job_success(mocker):
    mocker.patch("time.sleep", return_value=None)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    payload = {"some": "data"}
    
    result = run_backtest_job(mock_self, payload)
    
    assert result["status"] == "success"
    assert result["job_id"] == "test_job_id"
    assert result["payload_received"] == payload
