from __future__ import annotations
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Align with Story 2.3: worker truncates historical_range to 2-year lookback.
# Schema cap enforces the constraint at the contract boundary so payloads
# cannot request windows the worker will silently truncate.
HISTORICAL_RANGE_MAX_DAYS = 730  # 2 years, matches Story 2.3 lookback constraint
ASSETS_MAX_COUNT = 20  # aligns with /correlation endpoint cap


class InstrumentType(str, Enum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"

    def __str__(self) -> str:
        # Ensure f-string / str() yields the raw value (e.g. "SPOT"), not
        # "InstrumentType.SPOT". Downstream code logs and serializes these.
        return self.value


class Exchange(str, Enum):
    """Whitelisted exchanges. Extend as loaders are added."""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKX = "okx"
    # DEX
    UNISWAP = "uniswap"
    PANCAKESWAP = "pancakeswap"

    def __str__(self) -> str:
        return self.value


class GasFeeModel(str, Enum):
    """Gas fee estimation model. Must match DeFiSimulator.base_gas_costs keys."""
    DEFAULT = "default"
    DYNAMIC = "dynamic"
    STATIC = "static"

    def __str__(self) -> str:
        return self.value


class _StrictModel(BaseModel):
    """Base model that rejects unknown fields to catch client typos early."""
    model_config = ConfigDict(extra="forbid")


class SimulationEnvironment(_StrictModel):
    exchange: Exchange = Exchange.BINANCE
    instrument_type: InstrumentType = InstrumentType.SPOT
    initial_capital: Decimal = Field(..., gt=Decimal("0"))
    trading_fees: Decimal = Field(Decimal("0.001"), ge=Decimal("0"), le=Decimal("0.05"))
    slippage_tolerance: Decimal = Field(Decimal("0.001"), ge=Decimal("0"), le=Decimal("0.1"))
    historical_range: int = Field(730, ge=1, le=HISTORICAL_RANGE_MAX_DAYS)
    gas_fee_model: GasFeeModel = GasFeeModel.DEFAULT
    track_impermanent_loss: bool = True


class RiskManagement(_StrictModel):
    max_drawdown_percentage: Decimal = Field(Decimal("0.2"), ge=Decimal("0.01"), le=Decimal("1.0"))
    # stop_loss / take_profit are fractional percentages of entry price.
    # Cap at 1.0 (100%) to prevent runaway sentinel values like 9999.
    stop_loss: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1.0"))
    take_profit: Optional[Decimal] = Field(None, ge=Decimal("0"), le=Decimal("1.0"))
    position_sizing: Decimal = Field(Decimal("0.1"), ge=Decimal("0.01"), le=Decimal("1.0"))
    leverage: Decimal = Field(Decimal("1.0"), ge=Decimal("1.0"), le=Decimal("100.0"))


class ContextRules(_StrictModel):
    assets: List[str] = Field(..., min_length=1, max_length=ASSETS_MAX_COUNT)
    # Use lowercase m/h/d/w for minute/hour/day/week; uppercase M/Y for month/year.
    # Matches CCXT convention and disambiguates minute (m) vs month (M).
    timeframe: str = Field("1h", pattern=r"^\d+(m|h|d|w|M|Y)$")
    indicators: List[str] = Field(default_factory=list, max_length=50)
    natural_language_rules: Optional[str] = Field(None, max_length=10000)
    executable_code: Optional[str] = Field(None, max_length=50000)

    @field_validator("assets")
    @classmethod
    def _validate_asset_symbols(cls, value: List[str]) -> List[str]:
        cleaned: List[str] = []
        for raw in value:
            if not isinstance(raw, str):
                raise ValueError("Asset symbols must be strings")
            trimmed = raw.strip()
            if not trimmed:
                raise ValueError("Asset symbols cannot be empty or whitespace")
            if any(ch in trimmed for ch in ("\n", "\r", "\t")):
                raise ValueError(f"Asset symbol contains control characters: {raw!r}")
            if len(trimmed) > 32:
                raise ValueError(f"Asset symbol too long (max 32 chars): {trimmed}")
            cleaned.append(trimmed)
        return cleaned


class WFAConfig(_StrictModel):
    in_sample_periods: int = Field(5, ge=1)
    out_of_sample_periods: int = Field(1, ge=1)
    step_size: int = Field(1, ge=1)

    @model_validator(mode="after")
    def _validate_window_ratio(self) -> WFAConfig:
        if self.in_sample_periods <= self.out_of_sample_periods:
            raise ValueError(
                "in_sample_periods must be greater than out_of_sample_periods "
                "for walk-forward analysis to be meaningful"
            )
        return self


class ExecutionFlags(_StrictModel):
    enable_monte_carlo_stress_test: bool = False
    enable_rl_optimization: bool = False
    rl_max_trials: int = Field(50, ge=10, le=200)
    rl_optimization_target: str = Field("sharpe", pattern=r"^(sharpe|pnl|sortino)$")
    wfa_config: Optional[WFAConfig] = None


class VibeTradingJobPayload(_StrictModel):
    simulation_environment: SimulationEnvironment
    risk_management: RiskManagement
    context_rules: ContextRules
    execution_flags: ExecutionFlags

    @model_validator(mode="after")
    def validate_cross_fields(self) -> VibeTradingJobPayload:
        if self.simulation_environment.instrument_type == InstrumentType.SPOT:
            if self.risk_management.leverage > Decimal("1.0"):
                raise ValueError("Leverage greater than 1.0 is not supported for SPOT instruments.")
        return self


class PreviewResponse(_StrictModel):
    summary: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
