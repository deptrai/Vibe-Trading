import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from agent.api_server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_info():
    response = client.get("/api")
    assert response.status_code == 200
    assert "version" in response.json()

@patch("agent.api_server._configured_api_key")
@patch("agent.api_server._is_local_client")
def test_runs_requires_auth(mock_local, mock_api_key):
    mock_local.return_value = False
    mock_api_key.return_value = "secret"
    response = client.get("/runs")
    assert response.status_code == 403
