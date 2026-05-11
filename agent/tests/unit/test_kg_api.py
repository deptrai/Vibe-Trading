import pytest
from fastapi.testclient import TestClient
from api_server import app
import src.kg_store as kg_store_module
from src.kg_store import KnowledgeGraphStore

@pytest.fixture
def empty_store(tmp_path, monkeypatch):
    monkeypatch.setenv("API_AUTH_KEY", "test-secret-key")
    store = KnowledgeGraphStore(data_dir=str(tmp_path))
    store.events.clear()
    store.assets.clear()
    store.impacts.clear()
    store.correlations.clear()
    monkeypatch.setattr(kg_store_module, "_kg_store_instance", store)
    return store

@pytest.fixture
def client():
    # Pass auth key as a header if needed by api_server
    return TestClient(app)

def test_suggestions_empty_graph(client, empty_store):
    response = client.get("/api/v1/kg/suggestions", headers={"Authorization": "Bearer test-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) == 0
    assert data["total_events"] == 0

def test_kg_events_empty(client, empty_store):
    response = client.get("/api/v1/kg/events", headers={"Authorization": "Bearer test-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_kg_stats_empty(client, empty_store):
    response = client.get("/api/v1/kg/stats", headers={"Authorization": "Bearer test-secret-key"})
    assert response.status_code == 200
    data = response.json()
    assert data["num_events"] == 0
    assert data["num_assets"] == 0
