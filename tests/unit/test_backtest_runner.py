import pytest
from unittest.mock import patch
try:
    from agent.backtest.runner import BacktestRunner
except ImportError:
    BacktestRunner = None

@pytest.mark.skipif(BacktestRunner is None, reason="runner module missing")
def test_backtest_runner_initialization():
    runner = BacktestRunner(config={"initial_capital": 10000})
    assert runner.capital == 10000
