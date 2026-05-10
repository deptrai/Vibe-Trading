import pytest
import time
from fastapi.testclient import TestClient
from agent.api_server import app
from agent import api_server

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api_server, "_is_ip_whitelisted", lambda r: True)
    monkeypatch.setattr(api_server, "_API_KEY", "")
    return TestClient(app)

def test_preview_strategy(client):
    payload = {
        "simulation_environment": {
            "initial_capital": "15000",
            "historical_range": 365
        },
        "risk_management": {
            "max_drawdown_percentage": "0.15",
            "position_sizing": "0.2"
        },
        "context_rules": {
            "assets": ["BTC-USDT"],
            "timeframe": "1h",
            "natural_language_rules": "Buy when RSI is below 30"
        },
        "execution_flags": {}
    }
    
    start_time = time.time()
    response = client.post(
        "/preview", 
        json=payload,
        headers={"Authorization": "Bearer fake-token-for-test"}
    )
    end_time = time.time()
    
    # Missing Response Latency Verification Test
    latency_ms = (end_time - start_time) * 1000
    assert latency_ms < 500, f"Latency {latency_ms}ms exceeds 500ms SLA"
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "confidence_score" in data
    assert data["confidence_score"] == 0.95
    assert "BTC-USDT" in data["summary"]
    assert "Buy when RSI is below 30" in data["summary"]
    assert "20% position sizing" in data["summary"]
