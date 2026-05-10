import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.rl_worker import run_rl_optimization_job
from src.api_models import VibeTradingJobPayload

@pytest.fixture
def rl_payload():
    return {
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1d",
        },
        "simulation_environment": {
            "historical_range": 30,
            "exchange": "binance",
            "initial_capital": 10000,
            "instrument_type": "SPOT"
        },
        "execution_flags": {
            "enable_rl_optimization": True,
            "rl_max_trials": 10,
            "rl_optimization_target": "sharpe"
        },
        "risk_management": {
            "max_drawdown_percentage": 0.2,
            "leverage": 1.0
        }
    }

@patch("src.rl_worker.celery_app")
@patch("src.rl_optimizer.RLOptimizer")
@patch("backtest.loaders.registry.get_loader_cls_with_fallback")
def test_rl_worker_routing_and_execution(mock_get_loader, mock_optimizer_class, mock_celery, rl_payload):
    # Setup mocks
    mock_loader_instance = MagicMock()
    mock_get_loader.return_value = MagicMock(return_value=mock_loader_instance)
    mock_loader_instance.fetch.return_value = {"BTC/USDT": MagicMock()}
    
    mock_opt_instance = MagicMock()
    mock_opt_instance.optimize.return_value = {"status": "completed", "best_score": 1.5}
    mock_optimizer_class.return_value = mock_opt_instance
    
    # Run the worker directly
    class MockSelf:
        class Request:
            id = "test-job-id"
        request = Request()
        def update_state(self, *args, **kwargs):
            pass

    result = run_rl_optimization_job.__wrapped__.__func__(MockSelf(), rl_payload)
    
    # Verify
    assert result["status"] == "completed"
    assert result["best_score"] == 1.5
    
    mock_loader_instance.fetch.assert_called_once()
    mock_optimizer_class.assert_called_once()
    mock_opt_instance.optimize.assert_called_once()
    
    # Check max_trials was passed correctly
    opt_call_args = mock_optimizer_class.call_args[1]
    assert opt_call_args["max_trials"] == 10
    assert opt_call_args["target"] == "sharpe"

def test_rl_worker_timeout_handling():
    from celery.exceptions import SoftTimeLimitExceeded
    
    # Create an optimizer mock that raises SoftTimeLimitExceeded
    with patch("src.rl_optimizer.RLOptimizer") as mock_opt:
        mock_instance = MagicMock()
        mock_instance.optimize.side_effect = SoftTimeLimitExceeded("Time limit exceeded")
        mock_opt.return_value = mock_instance
        
        with patch("backtest.loaders.registry.get_loader_cls_with_fallback") as mock_get_loader:
            mock_loader = MagicMock()
            mock_loader.fetch.return_value = {"BTC/USDT": MagicMock()}
            mock_get_loader.return_value = MagicMock(return_value=mock_loader)
            
            class MockSelf:
                class Request:
                    id = "timeout-job"
                request = Request()
            
            # Use a basic payload
            payload = {
                "context_rules": {"assets": ["BTC/USDT"], "timeframe": "1d"},
                "simulation_environment": {"historical_range": 30, "exchange": "binance", "initial_capital": 10000, "instrument_type": "SPOT"},
                "execution_flags": {"enable_rl_optimization": True},
                "risk_management": {"max_drawdown_percentage": 0.2, "leverage": 1.0}
            }
            
            # Execute
            result = run_rl_optimization_job.__wrapped__.__func__(MockSelf(), payload)
            
            # Validate graceful handling
            assert result["status"] == "error"
            assert "Internal error" in result["message"]
