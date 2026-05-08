"""Unit tests for YFinance data loader."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from backtest.loaders.yfinance_loader import (
    DataLoader,
    _flatten_columns,
    _normalize_frame,
    _to_yfinance_interval,
    _to_yfinance_symbol,
)


class TestYFinanceHelpers:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("AAPL.US", "AAPL"),
            ("700.HK", "0700.HK"),
            ("9988.HK", "9988.HK"),
            ("BTC-USD", "BTC-USD"),
        ],
    )
    def test_to_yfinance_symbol(self, code: str, expected: str) -> None:
        assert _to_yfinance_symbol(code) == expected

    @pytest.mark.parametrize(
        "interval,expected",
        [
            ("1D", "1d"),
            ("1H", "1h"),
            ("4H", "1h"),
            ("5m", "5m"),
        ],
    )
    def test_to_yfinance_interval(self, interval: str, expected: str) -> None:
        assert _to_yfinance_interval(interval) == expected

    def test_flatten_columns_multiindex(self) -> None:
        cols = pd.MultiIndex.from_tuples([("Open", "AAPL"), ("Close", "AAPL")])
        df = pd.DataFrame([[1, 2]], columns=cols)
        flattened = _flatten_columns(df, "AAPL")
        assert list(flattened.columns) == ["Open", "Close"]

    def test_flatten_columns_single(self) -> None:
        df = pd.DataFrame([[1]], columns=["Open"])
        flattened = _flatten_columns(df, "AAPL")
        assert list(flattened.columns) == ["Open"]


class TestNormalizeFrame:
    def test_normalize_basic(self) -> None:
        df = pd.DataFrame(
            {
                "Open": [1.0],
                "High": [1.1],
                "Low": [0.9],
                "Close": [1.05],
                "Volume": [100],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        normalized = _normalize_frame(df, "1D")
        assert list(normalized.columns) == ["open", "high", "low", "close", "volume"]
        assert normalized.index.name == "trade_date"
        assert normalized.iloc[0]["open"] == 1.0

    def test_normalize_empty(self) -> None:
        df = pd.DataFrame()
        normalized = _normalize_frame(df, "1D")
        assert normalized.empty
        assert list(normalized.columns) == ["open", "high", "low", "close", "volume"]

    def test_normalize_tz_localization(self) -> None:
        df = pd.DataFrame(
            {
                "Open": [1.0],
                "High": [1.1],
                "Low": [0.9],
                "Close": [1.05],
                "Volume": [100],
            },
            index=pd.to_datetime(["2024-01-01 00:00:00+00:00"]),
        )
        normalized = _normalize_frame(df, "1H")
        assert normalized.index.tz is None


class TestYFinanceLoader:
    @patch("backtest.loaders.yfinance_loader._download_history")
    def test_fetch_single_symbol(self, mock_download: MagicMock) -> None:
        # Mocking bulk download
        mock_data = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [155.0],
                "Low": [149.0],
                "Close": [152.0],
                "Volume": [1000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        mock_download.return_value = mock_data

        loader = DataLoader()
        results = loader.fetch(["AAPL.US"], "2024-01-01", "2024-01-02")

        assert "AAPL.US" in results
        df = results["AAPL.US"]
        assert len(df) == 1
        assert df.iloc[0]["close"] == 152.0

    @patch("backtest.loaders.yfinance_loader._download_history")
    def test_fetch_multi_symbol(self, mock_download: MagicMock) -> None:
        # Mocking multi-index response from yfinance bulk download
        cols = pd.MultiIndex.from_tuples(
            [
                ("Open", "AAPL"),
                ("Open", "MSFT"),
                ("Close", "AAPL"),
                ("Close", "MSFT"),
                ("High", "AAPL"),
                ("High", "MSFT"),
                ("Low", "AAPL"),
                ("Low", "MSFT"),
                ("Volume", "AAPL"),
                ("Volume", "MSFT"),
            ]
        )
        data = [
            [150.0, 400.0, 152.0, 405.0, 155.0, 410.0, 149.0, 395.0, 1000, 2000]
        ]
        mock_data = pd.DataFrame(data, columns=cols, index=pd.to_datetime(["2024-01-01"]))
        mock_download.return_value = mock_data

        loader = DataLoader()
        results = loader.fetch(["AAPL.US", "MSFT.US"], "2024-01-01", "2024-01-02")

        assert "AAPL.US" in results
        assert "MSFT.US" in results
        assert results["AAPL.US"].iloc[0]["close"] == 152.0
        assert results["MSFT.US"].iloc[0]["close"] == 405.0

    @patch("backtest.loaders.yfinance_loader._download_history")
    def test_fetch_no_data(self, mock_download: MagicMock) -> None:
        mock_download.return_value = pd.DataFrame()
        loader = DataLoader()
        results = loader.fetch(["NONEXISTENT.US"], "2024-01-01", "2024-01-02")
        assert results == {}
