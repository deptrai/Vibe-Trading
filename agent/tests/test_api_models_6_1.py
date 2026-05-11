from decimal import Decimal
import pytest
from pydantic import ValidationError
from src.api_models import (
    VibeTradingJobPayload, 
    SimulationEnvironment, 
    RiskManagement, 
    ContextRules, 
    ExecutionFlags,
    InstrumentType,
    Exchange
)

def test_payload_validation_success_with_nl_rules():
    payload = {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": 10000.0,
        },
        "risk_management": {
            "leverage": 1.0,
            "position_sizing": 0.1
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1h",
            "executable_code": "pass",
            "natural_language_rules": "Buy when RSI < 30"
        },
        "execution_flags": {}
    }
    VibeTradingJobPayload(**payload)

def test_payload_validation_success_with_executable_code():
    payload = {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": 10000.0,
        },
        "risk_management": {
            "leverage": 1.0,
            "position_sizing": 0.1
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1h",
            "executable_code": "def next(self): pass"
        },
        "execution_flags": {}
    }
    VibeTradingJobPayload(**payload)

def test_payload_validation_fails_when_both_missing():
    payload = {
        "simulation_environment": {
            "exchange": "binance",
            "instrument_type": "SPOT",
            "initial_capital": 10000.0,
        },
        "risk_management": {
            "leverage": 1.0,
            "position_sizing": 0.1
        },
        "context_rules": {
            "assets": ["BTC/USDT"],
            "timeframe": "1h",
            # Both natural_language_rules and executable_code are missing
        },
        "execution_flags": {}
    }
    with pytest.raises(ValidationError) as excinfo:
        VibeTradingJobPayload(**payload)
    assert "Either natural_language_rules or executable_code must be provided" in str(excinfo.value)
