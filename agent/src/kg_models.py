from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os

# Phase 2 Feature Flag
ENABLE_MACRO_KG = os.environ.get("ENABLE_MACRO_KG", "false").lower() == "true"

class KGEvent(BaseModel):
    event_id: str
    title: str
    category: str  # "upgrade", "hack", "regulation", "listing", "halving", "depeg", "partnership"
    source: str
    url: Optional[str] = None
    timestamp: datetime
    summary: Optional[str] = None
    raw_categories: List[str] = Field(default_factory=list)

class KGAsset(BaseModel):
    asset_id: str  # e.g., "BTC", "ETH"
    symbol: str
    name: str
    chain: Optional[str] = None

class KGImpact(BaseModel):
    event_id: str
    asset_id: str
    weight: float = Field(..., ge=0.0, le=1.0)
    direction: str = Field(..., pattern=r"^(bullish|bearish|neutral)$")
    reason: str

class KGSuggestion(BaseModel):
    asset_symbol: str
    asset_name: str
    events: List[dict]  # [{event_title, weight, direction, reason, timestamp}]
    aggregate_score: float  # sum of weights, capped at 1.0
    suggested_action: str  # "monitor", "consider_long", "consider_short", "high_alert"

class KGSuggestionsResponse(BaseModel):
    suggestions: List[KGSuggestion]
    last_sync: Optional[datetime] = None
    total_events: int = 0
    total_assets: int = 0
