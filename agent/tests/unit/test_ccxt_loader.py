"""Unit tests for CCXT crypto data loader."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from backtest.loaders.ccxt_loader import DataLoader


class TestCCXTLoader:
    @patch("ccxt.binance")
    def test_get_exchange_default(self, mock_binance: MagicMock) -> None:
        loader = DataLoader()
        with patch.dict(os.environ, {}, clear=True):
            loader._get_exchange()
            mock_binance.assert_called_once()

    @patch("ccxt.okx")
    def test_get_exchange_env(self, mock_okx: MagicMock) -> None:
        loader = DataLoader()
        with patch.dict(os.environ, {"CCXT_EXCHANGE": "okx"}):
            loader._get_exchange()
            mock_okx.assert_called_once()

    def test_fetch_one_pagination(self) -> None:
        mock_exchange = MagicMock()
        # Mocking two pages of data
        # Page 1 must have 1000 rows to trigger next fetch (since limit=1000 is hardcoded)
        page1 = [[1704067200000 + i, 42000.0, 43000.0, 41000.0, 42500.0, 100.0] for i in range(1000)]
        page2 = [
            [1704153600000, 42500.0, 44000.0, 42000.0, 43500.0, 120.0],  # 2024-01-02
        ]
        mock_exchange.fetch_ohlcv.side_effect = [page1, page2, []]

        since_ms = 1704067200000
        end_ms = 1704240000000  # 2024-01-03

        loader = DataLoader()
        df = loader._fetch_one(mock_exchange, "BTC/USDT", "1d", since_ms, end_ms)

        assert df is not None
        assert len(df) > 1000
        assert mock_exchange.fetch_ohlcv.call_count == 2

    def test_fetch_one_empty(self) -> None:
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv.return_value = []
        loader = DataLoader()
        df = loader._fetch_one(mock_exchange, "BTC/USDT", "1d", 0, 1000000)
        assert df is None

    @patch.object(DataLoader, "_get_exchange")
    @patch.object(DataLoader, "_fetch_one")
    def test_fetch_integration(self, mock_fetch_one: MagicMock, mock_get_exchange: MagicMock) -> None:
        mock_exchange = MagicMock()
        mock_get_exchange.return_value = mock_exchange
        
        mock_df = pd.DataFrame(
            {
                "open": [40000.0],
                "high": [41000.0],
                "low": [39000.0],
                "close": [40500.0],
                "volume": [10.0],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        mock_fetch_one.return_value = mock_df

        loader = DataLoader()
        results = loader.fetch(["BTC-USDT"], "2024-01-01", "2024-01-02")

        assert "BTC-USDT" in results
        assert results["BTC-USDT"].iloc[0]["close"] == 40500.0
        # Check symbol conversion
        mock_fetch_one.assert_called_once()
        args = mock_fetch_one.call_args[0]
        assert args[1] == "BTC/USDT"
