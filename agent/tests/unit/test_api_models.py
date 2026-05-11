import pytest
from pydantic import ValidationError
from decimal import Decimal
from src.api_models import (
    VibeTradingJobPayload,
    SimulationEnvironment,
    RiskManagement,
    ContextRules,
    ExecutionFlags,
    InstrumentType,
)

def get_valid_payload():
    return VibeTradingJobPayload(
        simulation_environment=SimulationEnvironment(
            exchange="binance",
            instrument_type=InstrumentType.SPOT,
            initial_capital=Decimal("1000"),
            trading_fees=Decimal("0.001"),
            slippage_tolerance=Decimal("0.001"),
            historical_range=30,
        ),
        risk_management=RiskManagement(
            max_drawdown_percentage=Decimal("0.2"),
            position_sizing=Decimal("0.1"),
            leverage=Decimal("1.0"),
        ),
        context_rules=ContextRules(
            assets=["BTC-USDT"],
            timeframe="1h",
            natural_language_rules="Buy when price crosses SMA(20)"
        ),
        execution_flags=ExecutionFlags()
    )

def test_valid_payload():
    payload = get_valid_payload()
    assert payload.simulation_environment.exchange == "binance"

def test_invalid_spot_leverage():
    payload_data = get_valid_payload().model_dump()
    payload_data["risk_management"]["leverage"] = Decimal("2.0")
    
    with pytest.raises(ValidationError) as exc_info:
        VibeTradingJobPayload(**payload_data)
        
    assert "Leverage greater than 1.0 is not supported for SPOT instruments." in str(exc_info.value)

def test_valid_perpetual_leverage():
    payload_data = get_valid_payload().model_dump()
    payload_data["simulation_environment"]["instrument_type"] = "PERPETUAL"
    payload_data["risk_management"]["leverage"] = Decimal("10.0")
    
    payload = VibeTradingJobPayload(**payload_data)
    assert payload.risk_management.leverage == Decimal("10.0")

def test_missing_code_sources():
    payload_data = get_valid_payload().model_dump()
    payload_data["context_rules"]["natural_language_rules"] = None
    payload_data["context_rules"]["executable_code"] = None
    
    with pytest.raises(ValidationError) as exc_info:
        VibeTradingJobPayload(**payload_data)
        
    assert "Either natural_language_rules or executable_code must be provided" in str(exc_info.value)

def test_valid_executable_code():
    payload_data = get_valid_payload().model_dump()
    payload_data["context_rules"]["natural_language_rules"] = None
    payload_data["context_rules"]["executable_code"] = "print('hello world')"
    
    payload = VibeTradingJobPayload(**payload_data)
    assert payload.context_rules.executable_code == "print('hello world')"
