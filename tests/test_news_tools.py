"""
tests/test_news_tools.py
------------------------
Unit tests for news tools and NewsService.
Mocks HTTP request calls to avoid live API queries.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.news_service import NewsService
from app.tools import news_tools


@pytest.fixture
def mock_cryptopanic_response():
    """Create a mock JSON response for CryptoPanic."""
    return {
        "results": [
            {
                "title": "Bitcoin Surges past $50k",
                "published_at": "2026-08-17T12:00:00Z",
                "url": "https://cryptopanic.com/news/1",
                "source": {"title": "CoinJournal"}
            },
            {
                "title": "Regulators propose new rules",
                "published_at": "2026-08-17T13:00:00Z",
                "url": "https://cryptopanic.com/news/2",
                "source": {"title": "Blockworks"}
            }
        ]
    }


@pytest.fixture
def mock_newsapi_response():
    """Create a mock JSON response for NewsAPI."""
    return {
        "articles": [
            {
                "title": "Ethereum upgrade details released",
                "description": "Devs announced details on the upcoming hardfork.",
                "publishedAt": "2026-08-17T14:00:00Z",
                "url": "https://newsapi.org/news/1",
                "source": {"name": "CoinDesk"}
            }
        ]
    }


class TestNewsService:
    """Tests for NewsService class."""

    @patch('app.services.news_service.requests.get')
    def test_fetch_news_cryptopanic(self, mock_get, mock_cryptopanic_response):
        """Test fetching news from CryptoPanic API when key is enabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_cryptopanic_response
        mock_get.return_value = mock_response

        # Enable key config
        with patch('app.services.news_service.CRYPTOPANIC_API_KEY', 'test_cryptopanic_key'):
            service = NewsService()
            articles = service.fetch_news("BTC", limit=5)

            assert len(articles) == 2
            assert articles[0]['title'] == "Bitcoin Surges past $50k"
            assert articles[0]['source'] == "CoinJournal"
            assert articles[0]['url'] == "https://cryptopanic.com/news/1"

    @patch('app.services.news_service.requests.get')
    def test_fetch_news_newsapi_fallback(self, mock_get, mock_newsapi_response):
        """Test fallback to NewsAPI when CryptoPanic is not configured but NewsAPI is."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        # Set CryptoPanic key empty, but NewsAPI active
        with patch('app.services.news_service.CRYPTOPANIC_API_KEY', ''), \
             patch('app.services.news_service.NEWS_API_KEY', 'test_newsapi_key'):
            
            service = NewsService()
            articles = service.fetch_news("ETH", limit=5)

            assert len(articles) == 1
            assert articles[0]['title'] == "Ethereum upgrade details released"
            assert articles[0]['source'] == "CoinDesk"

    def test_fetch_news_disabled(self):
        """Test news fetching returns empty list when disabled."""
        with patch('app.services.news_service.NEWS_API_ENABLED', False):
            service = NewsService()
            articles = service.fetch_news("BTC")
            assert len(articles) == 0


class TestNewsTools:
    """Tests for LangChain news tools."""

    @patch('app.tools.news_tools.get_news_service')
    def test_search_crypto_news_tool(self, mock_get_service):
        """Test search_crypto_news tool output format."""
        mock_service = Mock()
        mock_service.fetch_news.return_value = [
            {
                "title": "Solana breaks speed record",
                "source": "SolanaInsider",
                "url": "https://solana.com/news/1",
                "published_at": "2026-08-17T15:00:00Z"
            }
        ]
        mock_get_service.return_value = mock_service

        result = news_tools.search_crypto_news.invoke({
            "symbol": "SOL/USDT",
            "limit": 5
        })

        assert "SOL" in result
        assert "breaks speed record" in result
        assert "SolanaInsider" in result
        mock_service.fetch_news.assert_called_once_with("SOL", limit=5)


class TestNewsToolsIntegration:
    """Integration tests for tool schema and registration."""

    def test_tool_is_structured_tool(self):
        """Test that search_crypto_news is a StructuredTool instance."""
        from langchain_core.tools import StructuredTool
        
        assert isinstance(news_tools.search_crypto_news, StructuredTool)

    def test_tool_registered_in_registry(self):
        """Test that the tool is registered in the central registry."""
        from app.tools import get_registry
        
        registry = get_registry()
        assert "search_crypto_news" in registry.get_names()
