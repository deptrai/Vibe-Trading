import pytest
import os
import ipaddress
from fastapi import HTTPException
from unittest.mock import MagicMock
import api_server

@pytest.fixture(autouse=True)
def reset_cached_networks():
    # Reset the cache before each test
    api_server._cached_allowed_ips = None
    yield
    api_server._cached_allowed_ips = None

def test_ip_whitelist_allowed(monkeypatch):
    request = MagicMock()
    request.client.host = "192.168.1.100"
    request.headers.get.return_value = None
    
    with monkeypatch.context() as m:
        m.setenv("ALLOWED_IPS", "192.168.1.100")
        assert api_server._is_ip_whitelisted(request) == True

def test_ip_whitelist_blocked(monkeypatch):
    request = MagicMock()
    request.client.host = "1.2.3.4"
    request.headers.get.return_value = None
    
    with monkeypatch.context() as m:
        m.setenv("ALLOWED_IPS", "192.168.1.100")
        assert api_server._is_ip_whitelisted(request) == False

def test_ip_whitelist_proxy_header(monkeypatch):
    request = MagicMock()
    request.client.host = "10.0.0.1" # Proxy IP
    request.headers.get.side_effect = lambda k: "192.168.1.100, 203.0.113.1" if k == "x-forwarded-for" else None
    
    with monkeypatch.context() as m:
        m.setenv("ALLOWED_IPS", "192.168.1.100")
        assert api_server._is_ip_whitelisted(request) == True

def test_ip_whitelist_subnet_parsing(monkeypatch):
    request = MagicMock()
    # Host IP inside subnet
    request.client.host = "192.168.1.50"
    request.headers.get.return_value = None
    
    with monkeypatch.context() as m:
        # Pass subnet with host bits, strict=False should handle it
        m.setenv("ALLOWED_IPS", "192.168.1.50/24")
        assert api_server._is_ip_whitelisted(request) == True

def test_ip_whitelist_malformed_entries(monkeypatch):
    request = MagicMock()
    request.client.host = "192.168.1.100"
    request.headers.get.return_value = None
    
    with monkeypatch.context() as m:
        # Invalid entries should be ignored
        m.setenv("ALLOWED_IPS", "invalid_ip, 192.168.1.100, ,")
        assert api_server._is_ip_whitelisted(request) == True

def test_ip_whitelist_ipv6_mismatch(monkeypatch):
    request = MagicMock()
    request.client.host = "2001:db8::1" # IPv6
    request.headers.get.return_value = None
    
    with monkeypatch.context() as m:
        # IPv4 allowed IPs
        m.setenv("ALLOWED_IPS", "192.168.1.0/24")
        # Should gracefully return False, not raise TypeError
        assert api_server._is_ip_whitelisted(request) == False

def test_validate_api_auth_requires_whitelisted_ip(monkeypatch):
    request = MagicMock()
    request.client.host = "1.2.3.4" # Not whitelisted
    request.headers.get.return_value = None
    
    # Not a local client
    with monkeypatch.context() as m:
        m.setattr(api_server, "_is_local_client", lambda r: False)
        m.setenv("ALLOWED_IPS", "192.168.1.100")
        
        with pytest.raises(HTTPException) as exc:
            api_server._validate_api_auth(request=request, cred=None)
        assert exc.value.status_code == 403
        assert "Access denied from this IP" in exc.value.detail

def test_validate_api_auth_passes_when_whitelisted(monkeypatch):
    request = MagicMock()
    request.client.host = "192.168.1.100" # Whitelisted
    request.headers.get.return_value = None
    
    with monkeypatch.context() as m:
        m.setattr(api_server, "_is_local_client", lambda r: False)
        m.setenv("ALLOWED_IPS", "192.168.1.100")
        m.setattr(api_server, "_API_KEY", "") # No API key configured
        
        # Should not raise exception
        api_server._validate_api_auth(request=request, cred=None)
