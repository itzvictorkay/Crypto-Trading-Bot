"""
tests/test_sentiment_tools.py
-----------------------------
Unit tests for sentiment tools and SentimentService.
Mocks the LangChain LLM output to avoid network calls.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.sentiment_service import SentimentService
from app.tools import sentiment_tools


from langchain_core.messages import AIMessage

@pytest.fixture
def mock_llm_response():
    """Create a mocked response matching the SentimentAnalysisResult schema."""
    text_data = (
        '{"sentiment": "POSITIVE", '
        '"confidence": 0.85, '
        '"reasoning": "Market sentiment is positive due to rising regulatory support.", '
        '"positive_score": 0.80, '
        '"negative_score": 0.05, '
        '"neutral_score": 0.15}'
    )
    return AIMessage(content=text_data)


class TestSentimentService:
    """Tests for SentimentService class."""

    @patch('app.services.sentiment_service.get_llm')
    def test_analyze_headlines_success(self, mock_get_llm, mock_llm_response):
        """Test successful headlines sentiment classification."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_llm.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm
        
        service = SentimentService(llm=mock_llm)
        headlines = [
            "Bitcoin adoption rises worldwide",
            "Institutional buying increases"
        ]
        
        result = service.analyze_headlines("BTC", headlines)
        
        assert result is not None
        assert result["sentiment"] == "POSITIVE"
        assert result["confidence"] == 0.85
        assert result["positive_score"] == 0.80
        assert result["negative_score"] == 0.05
        assert result["neutral_score"] == 0.15
        assert "regulatory support" in result["reasoning"]

    def test_analyze_headlines_empty_list(self):
        """Test sentiment classification with an empty headlines list."""
        service = SentimentService()
        result = service.analyze_headlines("BTC", [])
        
        assert result["sentiment"] == "NEUTRAL"
        assert result["confidence"] == 1.0
        assert result["positive_score"] == 0.0
        assert result["negative_score"] == 0.0
        assert result["neutral_score"] == 1.0


class TestSentimentTools:
    """Tests for LangChain sentiment tools."""

    @patch('app.tools.sentiment_tools.get_sentiment_service')
    def test_analyze_news_sentiment_tool(self, mock_get_service):
        """Test analyze_news_sentiment tool."""
        mock_service = Mock()
        mock_service.analyze_headlines.return_value = {
            "sentiment": "NEGATIVE",
            "confidence": 0.90,
            "reasoning": "Concerns over regulatory clampdowns in major markets.",
            "positive_score": 0.05,
            "neutral_score": 0.10,
            "negative_score": 0.85
        }
        mock_get_service.return_value = mock_service
        
        result = sentiment_tools.analyze_news_sentiment.invoke({
            "coin": "ETH",
            "headlines": "Ethereum gas fees skyrocket; Regulator opens investigation into developers"
        })
        
        assert "NEGATIVE" in result
        assert "90.0%" in result
        assert "regulatory clampdowns" in result
        mock_service.analyze_headlines.assert_called_once_with(
            "ETH", 
            ["Ethereum gas fees skyrocket", "Regulator opens investigation into developers"]
        )

    def test_analyze_news_sentiment_empty_input(self):
        """Test analyze_news_sentiment tool handles empty headlines gracefully."""
        result = sentiment_tools.analyze_news_sentiment.invoke({
            "coin": "BTC",
            "headlines": "   "
        })
        assert "Error" in result


class TestSentimentToolsIntegration:
    """Integration tests for tool schema and registration."""

    def test_tool_is_structured_tool(self):
        """Test that analyze_news_sentiment is a StructuredTool instance."""
        from langchain_core.tools import StructuredTool
        
        assert isinstance(sentiment_tools.analyze_news_sentiment, StructuredTool)

    def test_tool_registered_in_registry(self):
        """Test that the tool is registered in the central registry."""
        from app.tools import get_registry
        
        registry = get_registry()
        assert "analyze_news_sentiment" in registry.get_names()
