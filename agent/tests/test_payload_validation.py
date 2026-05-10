import sys
from unittest.mock import MagicMock
sys.modules["celery"] = MagicMock()

import pytest
from fastapi.testclient import TestClient
from agent.api_server import app, _is_local_client

@pytest.fixture
def client(monkeypatch):
    # Mock _is_local_client to always return True for tests
    # This bypasses the API_AUTH_KEY requirement logic for loopback clients
    monkeypatch.setattr("agent.api_server._is_local_client", lambda r: True)
    return TestClient(app)

def test_valid_payload(client):
    payload = {
        "simulation_environment": {
            "initial_capital": "10000.0",
            "historical_range": 730
        },
        "risk_management": {
            "max_drawdown_percentage": "0.2"
        },
        "context_rules": {
            "assets": ["BTC-USDT"],
            "timeframe": "1h"
        },
        "execution_flags": {}
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

def test_invalid_payload_capital(client):
    payload = {
        "simulation_environment": {
            "initial_capital": "-100" # Invalid capital
        },
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {}
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422

def test_invalid_payload_leverage_on_spot(client):
    payload = {
        "simulation_environment": {
            "instrument_type": "SPOT",
            "initial_capital": "10000.0",
            "historical_range": 730
        },
        "risk_management": {
            "leverage": "5.0" # Invalid for SPOT
        },
        "context_rules": {
            "assets": ["BTC-USDT"]
        },
        "execution_flags": {}
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
