from __future__ import annotations

import json
import logging
import os
import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone
from src.kg_models import KGEvent, KGAsset, KGImpact, KGSuggestion

logger = logging.getLogger(__name__)

# Guardrails from spec — prevent unbounded memory growth
MAX_EVENTS = 1000
MAX_ASSETS = 200

class KnowledgeGraphStore:
    def __init__(self, data_dir: str = "kg_data"):
        self.data_dir = data_dir
        self.filepath = os.path.join(data_dir, "graph.json")
        self.lock = threading.RLock()
        
        # In-memory storage
        self.events: Dict[str, KGEvent] = {}
        self.assets: Dict[str, KGAsset] = {}
        # adjacency lists
        # event_id -> list of impacts
        self.impacts: Dict[str, List[KGImpact]] = {}
        # asset_id -> list of correlations (asset_b, weight, category)
        self.correlations: Dict[str, List[dict]] = {}
        self.last_sync: Optional[datetime] = None

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        self.load()

    def add_event(self, event: KGEvent) -> None:
        with self.lock:
            if len(self.events) >= MAX_EVENTS and event.event_id not in self.events:
                # Evict oldest event to stay within guardrail
                oldest_id = min(self.events, key=lambda k: self.events[k].timestamp)
                del self.events[oldest_id]
                self.impacts.pop(oldest_id, None)
                logger.warning(f"KG guardrail: evicted oldest event {oldest_id} (max {MAX_EVENTS})")
            self.events[event.event_id] = event

    def add_asset(self, asset: KGAsset) -> None:
        with self.lock:
            if len(self.assets) >= MAX_ASSETS and asset.asset_id not in self.assets:
                logger.warning(f"KG guardrail: max assets ({MAX_ASSETS}) reached, skipping {asset.asset_id}")
                return
            self.assets[asset.asset_id] = asset

    def add_impact(self, event_id: str, asset_id: str, weight: float, direction: str, reason: str) -> None:
        with self.lock:
            if event_id not in self.impacts:
                self.impacts[event_id] = []
            
            # Check for existing impact to avoid duplicates
            for impact in self.impacts[event_id]:
                if impact.asset_id == asset_id:
                    impact.weight = weight
                    impact.direction = direction
                    impact.reason = reason
                    return

            self.impacts[event_id].append(
                KGImpact(event_id=event_id, asset_id=asset_id, weight=weight, direction=direction, reason=reason)
            )

    def add_correlation(self, asset_a: str, asset_b: str, weight: float, category: str) -> None:
        with self.lock:
            if asset_a not in self.correlations:
                self.correlations[asset_a] = []
            
            for corr in self.correlations[asset_a]:
                if corr['asset_id'] == asset_b:
                    corr['weight'] = weight
                    corr['category'] = category
                    return

            self.correlations[asset_a].append({
                "asset_id": asset_b,
                "weight": weight,
                "category": category
            })
            
            # Add bidirectional correlation
            if asset_b not in self.correlations:
                self.correlations[asset_b] = []
            
            for corr in self.correlations[asset_b]:
                if corr['asset_id'] == asset_a:
                    corr['weight'] = weight
                    corr['category'] = category
                    return
            
            self.correlations[asset_b].append({
                "asset_id": asset_a,
                "weight": weight,
                "category": category
            })

    def get_suggestions(self, limit: int = 10, min_weight: float = 0.3) -> List[KGSuggestion]:
        with self.lock:
            asset_scores: Dict[str, float] = {}
            asset_events: Dict[str, List[dict]] = {}
            
            for event_id, impacts in self.impacts.items():
                event = self.events.get(event_id)
                if not event:
                    continue
                    
                for impact in impacts:
                    if impact.weight < min_weight:
                        continue
                        
                    asset_id = impact.asset_id
                    
                    if asset_id not in asset_scores:
                        asset_scores[asset_id] = 0.0
                        asset_events[asset_id] = []
                        
                    # bullish adds, bearish subtracts (simplified logic for scoring)
                    score_delta = impact.weight if impact.direction == "bullish" else -impact.weight if impact.direction == "bearish" else 0.0
                    
                    # Store absolute weight for sorting by magnitude of impact
                    asset_scores[asset_id] += abs(score_delta)
                    
                    # Fix: Ensure timestamp has timezone info before calling isoformat
                    ts = event.timestamp
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    
                    asset_events[asset_id].append({
                        "event_title": event.title,
                        "weight": impact.weight,
                        "direction": impact.direction,
                        "reason": impact.reason,
                        "timestamp": ts.isoformat()
                    })

            suggestions = []
            for asset_id, score in asset_scores.items():
                asset = self.assets.get(asset_id)
                if not asset:
                    continue
                
                # cap score at 1.0 for the API model
                capped_score = min(score, 1.0)
                
                # determine action
                bullish_count = sum(1 for e in asset_events[asset_id] if e["direction"] == "bullish")
                bearish_count = sum(1 for e in asset_events[asset_id] if e["direction"] == "bearish")
                
                if bullish_count > bearish_count and score > 0.6:
                    action = "consider_long"
                elif bearish_count > bullish_count and score > 0.6:
                    action = "consider_short"
                elif score > 0.8:
                    action = "high_alert"
                else:
                    action = "monitor"

                suggestions.append(
                    KGSuggestion(
                        asset_symbol=asset.symbol,
                        asset_name=asset.name,
                        events=asset_events[asset_id],
                        aggregate_score=capped_score,
                        suggested_action=action
                    )
                )

            # sort by aggregate score descending
            suggestions.sort(key=lambda x: x.aggregate_score, reverse=True)
            return suggestions[:limit]

    def get_asset_impacts(self, symbol: str) -> List[dict]:
        with self.lock:
            # find asset id
            target_asset_id = None
            for asset_id, asset in self.assets.items():
                if asset.symbol.upper() == symbol.upper():
                    target_asset_id = asset_id
                    break
            
            if not target_asset_id:
                return []
            
            impacts_list = []
            for event_id, impacts in self.impacts.items():
                for impact in impacts:
                    if impact.asset_id == target_asset_id:
                        event = self.events.get(event_id)
                        if event:
                            impacts_list.append({
                                "event": event.model_dump(),
                                "impact": impact.model_dump()
                            })
            return impacts_list

    def get_recent_events(self, hours: int = 24) -> List[KGEvent]:
        with self.lock:
            now = datetime.now(timezone.utc)
            recent_events = []
            for event in self.events.values():
                ts = event.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                time_diff = (now - ts).total_seconds() / 3600
                if time_diff <= hours:
                    recent_events.append(event)
            
            recent_events.sort(key=lambda x: x.timestamp, reverse=True)
            return recent_events

    def save(self) -> None:
        with self.lock:
            last_sync_iso = None
            if self.last_sync:
                ts = self.last_sync
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                last_sync_iso = ts.isoformat()
                
            data = {
                "events": {k: v.model_dump(mode='json') for k, v in self.events.items()},
                "assets": {k: v.model_dump(mode='json') for k, v in self.assets.items()},
                "impacts": {k: [i.model_dump(mode='json') for i in v] for k, v in self.impacts.items()},
                "correlations": self.correlations,
                "last_sync": last_sync_iso
            }
            try:
                with open(self.filepath, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving knowledge graph to {self.filepath}: {e}")

    def load(self) -> None:
        with self.lock:
            if not os.path.exists(self.filepath):
                return
            
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                
                self.events = {k: KGEvent(**v) for k, v in data.get("events", {}).items()}
                self.assets = {k: KGAsset(**v) for k, v in data.get("assets", {}).items()}
                self.impacts = {k: [KGImpact(**i) for i in v] for k, v in data.get("impacts", {}).items()}
                self.correlations = data.get("correlations", {})
                last_sync_str = data.get("last_sync")
                if last_sync_str:
                    self.last_sync = datetime.fromisoformat(last_sync_str)
            except Exception as e:
                logger.error(f"Error loading knowledge graph from {self.filepath}: {e}")
                # Don't crash, just start empty

    def stats(self) -> dict:
        with self.lock:
            num_impacts = sum(len(impacts) for impacts in self.impacts.values())
            num_correlations = sum(len(corrs) for corrs in self.correlations.values()) // 2
            
            last_sync_iso = None
            if self.last_sync:
                ts = self.last_sync
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                last_sync_iso = ts.isoformat()
                
            return {
                "num_events": len(self.events),
                "num_assets": len(self.assets),
                "num_impacts": num_impacts,
                "num_correlations": num_correlations,
                "last_sync": last_sync_iso
            }

# Singleton instance
_kg_store_instance = None

def get_kg_store() -> KnowledgeGraphStore:
    global _kg_store_instance
    if _kg_store_instance is None:
        # Resolve path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), "kg_data")
        _kg_store_instance = KnowledgeGraphStore(data_dir=data_dir)
        
        # Auto-seed if empty
        if len(_kg_store_instance.assets) == 0:
            from src.kg_seed_data import seed_knowledge_graph
            seed_knowledge_graph()
            
    return _kg_store_instance
