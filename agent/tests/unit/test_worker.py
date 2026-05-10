import sys
from unittest.mock import MagicMock

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

def test_run_backtest_job_success(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda x: None)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    payload = {"some": "data"}
    
    result = run_backtest_job(mock_self, payload)
    
    assert result["status"] == "success"
    assert result["job_id"] == "test_job_id"
    assert result["payload_received"] == payload
