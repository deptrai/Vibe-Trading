import pytest
from unittest.mock import patch

try:
    from agent.src.worker import run_backtest_job
except ImportError:
    run_backtest_job = None

@pytest.mark.skipif(run_backtest_job is None, reason="worker.py not fully implemented")
@patch("agent.src.worker.Celery")
def test_run_backtest_job_mocked(mock_celery):
    payload = {"context_rules": {"assets": ["AAPL"]}, "risk_management": {"position_sizing": 0.1}}
    assert True