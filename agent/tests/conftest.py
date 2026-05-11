"""Shared fixtures and sys.path setup for all tests."""

from __future__ import annotations

import sys
import os
from pathlib import Path
import pytest

# Ensure agent/ is on sys.path so imports like `backtest.*` and `src.*` work.
AGENT_DIR = Path(__file__).resolve().parent.parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

# Clear environment variables before importing anything to avoid load_dotenv pollution
if "API_AUTH_KEY" in os.environ:
    del os.environ["API_AUTH_KEY"]

def pytest_configure(config):
    """Run before tests are collected to sanitize the environment."""
    if "API_AUTH_KEY" in os.environ:
        del os.environ["API_AUTH_KEY"]
    os.environ["VIBE_TRADING_TESTING"] = "1"

import api_server
import src.kg_store as kg_store_module

# Ensure module-level global is cleared even if loaded before conftest
api_server._API_KEY = ""
api_server._cached_allowed_ips = None

@pytest.fixture(autouse=True)
def restore_environ():
    """Restore os.environ to prevent pollution from load_dotenv()."""
    if "API_AUTH_KEY" in os.environ:
        del os.environ["API_AUTH_KEY"]
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    if "API_AUTH_KEY" in os.environ:
        del os.environ["API_AUTH_KEY"]

@pytest.fixture(autouse=True)
def reset_api_server_globals():
    """Reset module-level globals that cause test pollution."""
    api_server._API_KEY = ""
    api_server._cached_allowed_ips = None
    yield
    api_server._API_KEY = ""
    api_server._cached_allowed_ips = None

@pytest.fixture(autouse=True)
def reset_kg_store():
    """Reset KG store singleton between tests."""
    original = kg_store_module._kg_store_instance
    yield
    kg_store_module._kg_store_instance = original
