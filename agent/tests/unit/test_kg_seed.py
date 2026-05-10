import pytest
import os
from src.kg_store import KnowledgeGraphStore
from src.kg_seed_data import seed_knowledge_graph
import src.kg_store as kg_store_module

def test_seed_data_loading(tmp_path, monkeypatch):
    # Override the singleton to use a temporary store
    store = KnowledgeGraphStore(data_dir=str(tmp_path))
    monkeypatch.setattr(kg_store_module, "_kg_store_instance", store)
    
    # Run the seed function
    seed_knowledge_graph()
    
    # Verify graph is non-empty
    stats = store.stats()
    assert stats["num_assets"] > 0
    assert stats["num_events"] > 0
    assert stats["num_impacts"] > 0
    
    # Check for major assets
    assert "BTC" in store.assets
    assert "ETH" in store.assets
