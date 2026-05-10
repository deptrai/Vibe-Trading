from __future__ import annotations
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

class InstrumentType(str, Enum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"

class SimulationEnvironment(BaseModel):
    exchange: str = "binance"
    instrument_type: InstrumentType = InstrumentType.SPOT
    initial_capital: Decimal = Field(..., gt=Decimal('0'))
    trading_fees: Decimal = Field(Decimal('0.001'), ge=Decimal('0'), le=Decimal('0.05'))
    slippage_tolerance: Decimal = Field(Decimal('0.001'), ge=Decimal('0'), le=Decimal('0.1'))
    historical_range: int = Field(730, ge=1, le=3650)
    gas_fee_model: str = "default"
    track_impermanent_loss: bool = True

class RiskManagement(BaseModel):
    max_drawdown_percentage: Decimal = Field(Decimal('0.2'), ge=Decimal('0.01'), le=Decimal('1.0'))
    stop_loss: Optional[Decimal] = Field(None, ge=Decimal('0'))
    take_profit: Optional[Decimal] = Field(None, ge=Decimal('0'))
    position_sizing: Decimal = Field(Decimal('0.1'), ge=Decimal('0.01'), le=Decimal('1.0'))
    leverage: Decimal = Field(Decimal('1.0'), ge=Decimal('1.0'), le=Decimal('100.0'))

class ContextRules(BaseModel):
    assets: List[str] = Field(..., min_length=1)
    timeframe: str = Field("1h", pattern=r"^\d+[mhdwM]$")
    indicators: List[str] = []
    natural_language_rules: Optional[str] = Field(None, max_length=10000)
    executable_code: Optional[str] = Field(None, max_length=50000)

class WFAConfig(BaseModel):
    in_sample_periods: int = Field(5, ge=1)
    out_of_sample_periods: int = Field(1, ge=1)
    step_size: int = Field(1, ge=1)

class ExecutionFlags(BaseModel):
    enable_monte_carlo_stress_test: bool = False
    enable_rl_optimization: bool = False
    wfa_config: Optional[WFAConfig] = None

class VibeTradingJobPayload(BaseModel):
    simulation_environment: SimulationEnvironment
    risk_management: RiskManagement
    context_rules: ContextRules
    execution_flags: ExecutionFlags

    @model_validator(mode='after')
    def validate_cross_fields(self) -> VibeTradingJobPayload:
        if self.simulation_environment.instrument_type == InstrumentType.SPOT:
            if self.risk_management.leverage > Decimal('1.0'):
                raise ValueError("Leverage greater than 1.0 is not supported for SPOT instruments.")
        return self

class PreviewResponse(BaseModel):
    summary: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
