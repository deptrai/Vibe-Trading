import pytest
from unittest.mock import MagicMock
import agent.api_server as api_server

@pytest.fixture(autouse=True)
def reset_cached_ips():
    api_server._cached_allowed_ips = None
    yield
    api_server._cached_allowed_ips = None

def get_mock_request(host: str, forwarded_for: str = None):
    mock_req = MagicMock()
    if forwarded_for:
        mock_req.headers.get.return_value = forwarded_for
    else:
        mock_req.headers.get.return_value = None
    
    if host:
        mock_req.client.host = host
    else:
        mock_req.client = None
    return mock_req

def test_is_ip_whitelisted_empty_allowed(monkeypatch):
    monkeypatch.setenv("ALLOWED_IPS", "")
    req = get_mock_request(host="192.168.1.1")
    assert api_server._is_ip_whitelisted(req) is False

def test_is_ip_whitelisted_valid_ip(monkeypatch):
    monkeypatch.setenv("ALLOWED_IPS", "192.168.1.0/24, 10.0.0.1")
    req = get_mock_request(host="192.168.1.100")
    assert api_server._is_ip_whitelisted(req) is True
    
    req_exact = get_mock_request(host="10.0.0.1")
    assert api_server._is_ip_whitelisted(req_exact) is True
    
    req_fail = get_mock_request(host="10.0.0.2")
    assert api_server._is_ip_whitelisted(req_fail) is False

def test_is_ip_whitelisted_forwarded_for(monkeypatch):
    monkeypatch.setenv("ALLOWED_IPS", "192.168.1.0/24")
    monkeypatch.setenv("IP_WHITELIST_TRUST_PROXY", "1")
    req = get_mock_request(host="10.0.0.1", forwarded_for="192.168.1.50, 203.0.113.1")
    assert api_server._is_ip_whitelisted(req) is True
