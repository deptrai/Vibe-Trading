import pytest
from unittest.mock import patch, MagicMock
from src.kg_crawler import fetch_cryptocompare_news, fetch_coingecko_news, sync_knowledge_graph
import requests

class TestKGCrawlerBackend:
    """[P1] Unit tests for KG Crawler network and error handling"""

    @patch("src.kg_crawler.requests.get")
    def test_fetch_cryptocompare_success(self, mock_get):
        """[P1] should parse primary API successfully"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Data": [
                {
                    "id": "1", 
                    "title": "Bitcoin surges", 
                    "source_info": {"name": "News"}, 
                    "published_on": 1700000000,
                    "url": "http://example.com/1",
                    "body": "Bitcoin went up today."
                }
            ]
        }
        mock_get.return_value = mock_response

        events = fetch_cryptocompare_news()
        assert len(events) == 1
        assert events[0]["title"] == "Bitcoin surges"
        mock_get.assert_called_once()

    @patch("src.kg_crawler.requests.get")
    def test_fetch_coingecko_success(self, mock_get):
        """[P1] should handle CoinGecko stub gracefully"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        events = fetch_coingecko_news()
        # Stub returns empty list
        assert len(events) == 0
        mock_get.assert_called_once()

    @patch("src.kg_crawler.requests.get")
    def test_fetch_news_timeout_graceful(self, mock_get):
        """[P1] should handle network timeout without crashing"""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        events = fetch_cryptocompare_news()
        assert isinstance(events, list)
        assert len(events) == 0

    @patch("src.kg_crawler.requests.get")
    def test_sync_knowledge_graph_error_boundary(self, mock_get):
        """[P1] should not crash worker if ingestion fails unexpectedly"""
        # Assume an exception is raised due to parsing issue that wasn't caught
        mock_get.side_effect = Exception("Unexpected network parsing error")
        
        try:
            # When unexpected error occurs, fetch functions catch it
            result = sync_knowledge_graph()
            assert result == "failed"
        except Exception:
            pytest.fail("sync_knowledge_graph should handle exceptions gracefully")
