import pytest
from unittest.mock import MagicMock
import pandas as pd
from decimal import Decimal
from src.worker import run_backtest_job
from src.api_models import (
    VibeTradingJobPayload,
    SimulationEnvironment,
    RiskManagement,
    ContextRules,
    ExecutionFlags,
    InstrumentType,
)

@pytest.fixture
def base_payload():
    return {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": "1000",
            "trading_fees": "0.001",
            "slippage_tolerance": "0.001",
            "historical_range": 30
        },
        "risk_management": {
            "max_drawdown_percentage": "0.2",
            "position_sizing": "0.1",
            "leverage": "1.0"
        },
        "context_rules": {
            "assets": ["BTC-USDT"],
            "timeframe": "1h"
        },
        "execution_flags": {}
    }

def test_run_backtest_job_crypto_success(mocker, base_payload):
    # Mock ccxt loader
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    mock_loader_cls.return_value = mock_loader
    
    # Return fake dataframe
    fake_df = pd.DataFrame({"close": [1, 2]}, index=pd.date_range("2026-05-01", periods=2))
    mock_loader.fetch.return_value = {"BTC-USDT": fake_df}
    
    mocker.patch("src.worker.get_loader_cls_with_fallback", return_value=mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    
    result = run_backtest_job(mock_self, base_payload)
    
    assert result["status"] == "success"
    assert result["job_id"] == "test_job_id"
    assert "BTC-USDT" in result["data_summary"]
    mock_loader.fetch.assert_called_once()
    
    # Verify the code filtered and used the right symbol
    call_kwargs = mock_loader.fetch.call_args.kwargs
    assert call_kwargs["codes"] == ["BTC-USDT"]

def test_run_backtest_job_reject_non_crypto(mocker, base_payload):
    # Update payload to have only non-crypto
    base_payload["context_rules"]["assets"] = ["AAPL", "VNM"]
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    
    result = run_backtest_job(mock_self, base_payload)
    
    # Should reject gracefully
    assert result["status"] == "error"
    assert "No valid crypto assets provided" in result["message"]

def test_run_backtest_job_rate_limit_retry(mocker, base_payload):
    import ccxt
    # Mock ccxt loader to raise NetworkError
    mock_loader_cls = MagicMock()
    mock_loader = MagicMock()
    mock_loader_cls.return_value = mock_loader
    
    mock_loader.fetch.side_effect = ccxt.NetworkError("Rate limited!")
    
    mocker.patch("src.worker.get_loader_cls_with_fallback", return_value=mock_loader_cls)
    
    mock_self = MagicMock()
    mock_self.request.id = "test_job_id"
    
    with pytest.raises(ccxt.NetworkError):
        run_backtest_job(mock_self, base_payload)
