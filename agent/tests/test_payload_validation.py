"""Integration tests for /jobs payload validation.

Mocks Celery dispatch so tests don't require a live Redis/broker.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import api_server


@pytest.fixture
def client(monkeypatch):
    """Client that bypasses auth (loopback) and mocks Celery dispatch."""
    monkeypatch.setattr(api_server, "_is_local_client", lambda r: True)

    fake_task = SimpleNamespace(id="test-job-id-123")

    with patch("src.worker.run_backtest_job.apply_async", return_value=fake_task), \
         patch("src.rl_worker.run_rl_optimization_job.apply_async", return_value=fake_task):
        yield TestClient(api_server.app)


def test_valid_payload(client):
    payload = {
        "simulation_environment": {
            "initial_capital": "10000.0",
            "historical_range": 730,
        },
        "risk_management": {
            "max_drawdown_percentage": "0.2",
        },
        "context_rules": {
            "assets": ["BTC-USDT"],
            "timeframe": "1h",
            "executable_code": "pass",
        },
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["job_id"] == "test-job-id-123"


def test_invalid_payload_capital(client):
    payload = {
        "simulation_environment": {"initial_capital": "-100"},
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_invalid_payload_leverage_on_spot(client):
    payload = {
        "simulation_environment": {
            "instrument_type": "SPOT",
            "initial_capital": "10000.0",
        },
        "risk_management": {"leverage": "5.0"},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_extra_field_rejected(client):
    """Schema must reject unknown fields to catch client typos."""
    payload = {
        "simulation_environment": {
            "initial_capital": "10000.0",
            "unexpected_field": "some_value",
        },
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
    assert "unexpected_field" in response.text


def test_stop_loss_upper_bound(client):
    """stop_loss > 1.0 must be rejected (fractional percentage)."""
    payload = {
        "simulation_environment": {"initial_capital": "10000.0"},
        "risk_management": {"stop_loss": "9999"},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_historical_range_exceeds_two_year_cap(client):
    """historical_range > 730 days must be rejected per Story 2.3 constraint."""
    payload = {
        "simulation_environment": {
            "initial_capital": "10000.0",
            "historical_range": 3000,
        },
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_unknown_exchange_rejected(client):
    payload = {
        "simulation_environment": {
            "initial_capital": "10000.0",
            "exchange": "fake_exchange",
        },
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_empty_asset_symbol_rejected(client):
    payload = {
        "simulation_environment": {"initial_capital": "10000.0"},
        "risk_management": {},
        "context_rules": {"assets": ["  "]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_too_many_assets_rejected(client):
    payload = {
        "simulation_environment": {"initial_capital": "10000.0"},
        "risk_management": {},
        "context_rules": {"assets": [f"ASSET{i}-USDT" for i in range(25)]},
        "execution_flags": {},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_timeframe_minute_vs_month_disambiguation(client):
    """Both '5m' (minute) and '1M' (month) must validate."""
    base = {
        "simulation_environment": {"initial_capital": "10000.0"},
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {},
    }
    for tf in ("5m", "15m", "1h", "1d", "1w", "1M", "1Y"):
        payload = {**base, "context_rules": {**base["context_rules"], "timeframe": tf, "executable_code": "pass"}}
        response = client.post("/jobs", json=payload)
        assert response.status_code == 200, f"timeframe {tf!r} should be valid"


def test_wfa_config_requires_more_in_sample_than_out_of_sample(client):
    payload = {
        "simulation_environment": {"initial_capital": "10000.0"},
        "risk_management": {},
        "context_rules": {"assets": ["BTC-USDT"]},
        "execution_flags": {
            "wfa_config": {"in_sample_periods": 1, "out_of_sample_periods": 5}
        },
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422
