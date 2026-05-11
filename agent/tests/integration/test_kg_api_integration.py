import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from api_server import app
from src.kg_models import KGAsset, KGEvent
from src.kg_store import KnowledgeGraphStore
import src.kg_store as kg_store_module
from datetime import datetime, timezone

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-secret-key"}

@pytest.fixture
def populated_store(tmp_path, monkeypatch):
    store = KnowledgeGraphStore(data_dir=str(tmp_path))
    store.events.clear()
    store.assets.clear()
    store.impacts.clear()
    store.correlations.clear()
    
    store.add_asset(KGAsset(asset_id="BTC", symbol="BTC", name="Bitcoin"))
    store.add_asset(KGAsset(asset_id="ETH", symbol="ETH", name="Ethereum"))
    
    event1 = KGEvent(event_id="e1", title="BTC Halving", category="halving", source="News", timestamp=datetime.now(timezone.utc))
    event2 = KGEvent(event_id="e2", title="ETH Upgrade", category="upgrade", source="News", timestamp=datetime.now(timezone.utc))
    
    store.add_event(event1)
    store.add_event(event2)
    
    store.add_impact("e1", "BTC", 0.9, "bullish", "Halving")
    store.add_impact("e2", "ETH", 0.8, "bullish", "Upgrade")
    
    monkeypatch.setattr(kg_store_module, "_kg_store_instance", store)
    return store

@pytest.fixture
def client(monkeypatch):
    import api_server as _api_server
    monkeypatch.setattr(_api_server, "_is_ip_whitelisted", lambda r: True)
    monkeypatch.setattr(_api_server, "_API_KEY", "test-secret-key")
    return TestClient(app, raise_server_exceptions=False)

def test_get_suggestions_populated(client, populated_store, auth_headers):
    """[P1] should handle successful suggestion retrieval"""
    response = client.get("/api/v1/kg/suggestions?limit=10&min_weight=0.1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 2
    assert data["suggestions"][0]["asset_symbol"] == "BTC"

def test_get_suggestions_min_weight_filter(client, populated_store, auth_headers):
    """[P1] should filter suggestions below min_weight"""
    response = client.get("/api/v1/kg/suggestions?min_weight=0.85", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["asset_symbol"] == "BTC"

def test_get_events(client, populated_store, auth_headers):
    """[P1] should return events within the time window"""
    response = client.get("/api/v1/kg/events?hours=24", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_kg_stats(client, populated_store, auth_headers):
    """[P1] should return correct stats for populated graph"""
    response = client.get("/api/v1/kg/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["num_assets"] == 2
    assert data["num_events"] == 2

@patch("api_server.sync_knowledge_graph.delay")
def test_manual_sync_trigger(mock_delay, client, auth_headers):
    """[P1] should trigger manual sync and enqueue task"""
    response = client.post("/api/v1/kg/sync", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "triggered"
    mock_delay.assert_called_once()

@patch("src.kg_store.KnowledgeGraphStore.get_suggestions")
def test_suggestions_error_boundary(mock_get_suggestions, client, auth_headers):
    """[P2] should handle unexpected errors from store gracefully without hanging"""
    mock_get_suggestions.side_effect = Exception("Store corrupted")
    response = client.get("/api/v1/kg/suggestions", headers=auth_headers)
    # The app bubbles up the exception so testclient will get a 500 error 
    assert response.status_code == 500
