"""Unit tests for Backtest Runner logic."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from backtest.runner import (
    BacktestConfigSchema,
    _detect_market,
    _detect_source,
    _validate_signal_engine_source,
    main,
)


class TestConfigSchema:
    def test_valid_config(self) -> None:
        valid = {
            "codes": ["AAPL.US"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "source": "yfinance",
            "interval": "1D",
            "engine": "daily",
        }
        config = BacktestConfigSchema(**valid)
        assert config.codes == ["AAPL.US"]

    def test_invalid_date(self) -> None:
        invalid = {
            "codes": ["AAPL.US"],
            "start_date": "not-a-date",
            "end_date": "2024-12-31",
        }
        with pytest.raises(ValidationError):
            BacktestConfigSchema(**invalid)

    def test_start_after_end(self) -> None:
        invalid = {
            "codes": ["AAPL.US"],
            "start_date": "2024-12-31",
            "end_date": "2024-01-01",
        }
        with pytest.raises(ValidationError):
            BacktestConfigSchema(**invalid)

    def test_unsupported_interval(self) -> None:
        invalid = {
            "codes": ["AAPL.US"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "interval": "1Year",
        }
        with pytest.raises(ValidationError):
            BacktestConfigSchema(**invalid)


class TestMarketDetection:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("600519.SH", "a_share"),
            ("000001.SZ", "a_share"),
            ("AAPL.US", "us_equity"),
            ("700.HK", "hk_equity"),
            ("BTC-USDT", "crypto"),
            ("ETH/USDT", "crypto"),
            ("IF2406.CFFEX", "futures"),
            ("rb2410.SHFE", "futures"),
            ("ESZ4", "futures"),
            ("EUR/USD", "forex"),
            ("GBPUSD.FX", "forex"),
        ],
    )
    def test_detect_market(self, code: str, expected: str) -> None:
        assert _detect_market(code) == expected

    def test_detect_source(self) -> None:
        assert _detect_source("AAPL.US") == "yfinance"
        assert _detect_source("600519.SH") == "tushare"
        assert _detect_source("BTC-USDT") == "okx"


class TestSecurityValidation:
    def test_validate_safe_code(self, tmp_path: Path) -> None:
        safe_code = """
import pandas as pd

class SignalEngine:
    def __init__(self):
        self.name = "safe"
    
    def generate_signals(self, data):
        return []
"""
        f = tmp_path / "signal_engine.py"
        f.write_text(safe_code)
        # Should not raise
        _validate_signal_engine_source(f)

    def test_validate_unsafe_code(self, tmp_path: Path) -> None:
        unsafe_code = """
import os
os.system("rm -rf /") # Executable top-level statement

class SignalEngine:
    pass
"""
        f = tmp_path / "signal_engine.py"
        f.write_text(unsafe_code)
        with pytest.raises(ValueError, match="Executable top-level statement"):
            _validate_signal_engine_source(f)


class TestMainOrchestration:
    @patch("backtest.runner._load_module_from_file")
    @patch("backtest.runner._get_loader")
    @patch("backtest.runner._create_market_engine")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_main_flow(
        self,
        mock_read_text: MagicMock,
        mock_exists: MagicMock,
        mock_create_engine: MagicMock,
        mock_get_loader: MagicMock,
        mock_load_mod: MagicMock,
        tmp_path: Path,
    ) -> None:
        # Mocking existence of config and signal_engine
        mock_exists.return_value = True
        
        config_data = {
            "codes": ["AAPL.US"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "source": "yfinance",
        }
        mock_read_text.return_value = json.dumps(config_data)

        # Mock Loader
        mock_loader_instance = MagicMock()
        mock_loader_instance.fetch.return_value = {"AAPL.US": MagicMock()}
        mock_get_loader.return_value = MagicMock(return_value=mock_loader_instance)

        # Mock Signal Engine
        mock_signal_engine_cls = MagicMock()
        mock_signal_engine_mod = MagicMock()
        mock_signal_engine_mod.SignalEngine = mock_signal_engine_cls
        mock_load_mod.return_value = mock_signal_engine_mod

        # Mock Market Engine
        mock_market_engine = MagicMock()
        mock_create_engine.return_value = mock_market_engine

        # Run main
        main(tmp_path)

        # Verify orchestration
        mock_get_loader.assert_called_with("yfinance")
        mock_loader_instance.fetch.assert_called_once()
        mock_create_engine.assert_called()
        mock_market_engine.run_backtest.assert_called_once()
