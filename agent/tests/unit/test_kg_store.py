import pytest
import os
import json
from datetime import datetime, timezone
from src.kg_store import KnowledgeGraphStore
from src.kg_models import KGEvent, KGAsset

@pytest.fixture
def temp_kg_store(tmp_path):
    # Use a temporary directory for the store data
    store = KnowledgeGraphStore(data_dir=str(tmp_path))
    # Clear any auto-seeded data for clean tests
    store.events.clear()
    store.assets.clear()
    store.impacts.clear()
    store.correlations.clear()
    return store

def test_store_add_and_query(temp_kg_store):
    # Add an asset
    asset = KGAsset(asset_id="BTC", symbol="BTC", name="Bitcoin")
    temp_kg_store.add_asset(asset)
    
    # Add an event
    event = KGEvent(
        event_id="e1", 
        title="Bitcoin Halving", 
        category="halving", 
        source="Test News", 
        timestamp=datetime.now(timezone.utc)
    )
    temp_kg_store.add_event(event)
    
    # Add an impact
    temp_kg_store.add_impact("e1", "BTC", 0.9, "bullish", "Halving reduces supply")
    
    stats = temp_kg_store.stats()
    assert stats["num_assets"] == 1
    assert stats["num_events"] == 1
    assert stats["num_impacts"] == 1
    
    # Test query suggestions
    suggestions = temp_kg_store.get_suggestions(limit=10, min_weight=0.5)
    assert len(suggestions) == 1
    assert suggestions[0].asset_symbol == "BTC"
    assert suggestions[0].aggregate_score == 0.9
    assert suggestions[0].suggested_action in ["consider_long", "high_alert"]

def test_store_persistence(temp_kg_store, tmp_path):
    asset = KGAsset(asset_id="ETH", symbol="ETH", name="Ethereum")
    temp_kg_store.add_asset(asset)
    event = KGEvent(
        event_id="e2", 
        title="ETH Upgrade", 
        category="upgrade", 
        source="Test News", 
        timestamp=datetime.now(timezone.utc)
    )
    temp_kg_store.add_event(event)
    temp_kg_store.add_impact("e2", "ETH", 0.8, "bullish", "Upgrade improves scalability")
    
    temp_kg_store.last_sync = datetime.now(timezone.utc)
    temp_kg_store.save()
    
    # Load into a new instance
    new_store = KnowledgeGraphStore(data_dir=str(tmp_path))
    assert len(new_store.assets) == 1
    assert "ETH" in new_store.assets
    assert len(new_store.events) == 1
    assert "e2" in new_store.events
    assert len(new_store.impacts) == 1
    assert new_store.last_sync is not None

def test_get_suggestions_filtering_and_ranking(temp_kg_store):
    temp_kg_store.add_asset(KGAsset(asset_id="A1", symbol="A1", name="Asset 1"))
    temp_kg_store.add_asset(KGAsset(asset_id="A2", symbol="A2", name="Asset 2"))
    
    e1 = KGEvent(event_id="e1", title="Event 1", category="general", source="S", timestamp=datetime.now(timezone.utc))
    e2 = KGEvent(event_id="e2", title="Event 2", category="general", source="S", timestamp=datetime.now(timezone.utc))
    temp_kg_store.add_event(e1)
    temp_kg_store.add_event(e2)
    
    # A1 gets a weak impact
    temp_kg_store.add_impact("e1", "A1", 0.2, "bullish", "Weak")
    # A2 gets a strong impact
    temp_kg_store.add_impact("e2", "A2", 0.9, "bullish", "Strong")
    
    # min_weight=0.3 should filter out A1
    suggestions = temp_kg_store.get_suggestions(limit=10, min_weight=0.3)
    assert len(suggestions) == 1
    assert suggestions[0].asset_symbol == "A2"
    
    # min_weight=0.1 should include both, A2 ranked higher
    suggestions = temp_kg_store.get_suggestions(limit=10, min_weight=0.1)
    assert len(suggestions) == 2
    assert suggestions[0].asset_symbol == "A2"
    assert suggestions[1].asset_symbol == "A1"
