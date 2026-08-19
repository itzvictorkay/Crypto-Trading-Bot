"""
tests/test_agents.py
--------------------
Unit and integration tests for LangGraph multi-agent orchestrator and sub-agents.
Mocks all tool invocations and LLM responses to execute offline.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from langchain_core.messages import AIMessage

from app.agents import CryptoOrchestrator
from app.agents.market_agent import MarketAgent
from app.agents.news_agent import NewsAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.research_agent import ResearchAgent
from app.agents.risk_agent import RiskAgent
from app.agents.report_agent import ReportAgent


@pytest.fixture
def mock_llm_response():
    """Generic mocked AIMessage for LLM nodes."""
    return AIMessage(content="Mocked LLM Expert Analysis Summary Content")


class TestSubAgents:
    """Tests for each individual specialized agent."""

    @patch('app.agents.market_agent.get_llm')
    @patch('app.agents.market_agent.get_registry')
    @pytest.mark.anyio
    async def test_market_agent(self, mock_registry, mock_get_llm, mock_llm_response):
        """Test MarketAgent runs its tools and returns LLM synthesis."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm

        # Mock tools in registry
        price_tool = Mock()
        price_tool.name = "get_crypto_price"
        price_tool.invoke.return_value = "BTC/USDT Price: $45000"

        sr_tool = Mock()
        sr_tool.name = "get_support_resistance"
        sr_tool.invoke.return_value = "Support: $44000 | Resistance: $46000"

        ind_tool = Mock()
        ind_tool.name = "calculate_market_indicators"
        ind_tool.invoke.return_value = "Confluence Signal: BUY\nClose Price: $45000\nATR: 500"

        reg = Mock()
        reg.get.side_effect = lambda name: {
            "get_crypto_price": price_tool,
            "get_support_resistance": sr_tool,
            "calculate_market_indicators": ind_tool,
            "get_market_data": Mock(),
            "get_volume_stats": Mock()
        }[name]
        mock_registry.return_value = reg

        agent = MarketAgent()
        res = await agent.run(query="Analyze BTC", context={"coin": "BTC", "timeframe": "1h"})

        assert res["success"] is True
        assert res["analysis"] == "Mocked LLM Expert Analysis Summary Content"
        assert res["data"]["price_summary"] == "BTC/USDT Price: $45000"

    @patch('app.agents.news_agent.get_llm')
    @patch('app.agents.news_agent.get_registry')
    @pytest.mark.anyio
    async def test_news_agent(self, mock_registry, mock_get_llm, mock_llm_response):
        """Test NewsAgent runs news fetching and summaries."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm

        news_tool = Mock()
        news_tool.name = "search_crypto_news"
        news_tool.invoke.return_value = "1. Bitcoin reaches new heights"

        reg = Mock()
        reg.get.return_value = news_tool
        mock_registry.return_value = reg

        agent = NewsAgent()
        res = await agent.run(query="BTC news", context={"coin": "BTC"})

        assert res["success"] is True
        assert "Mocked" in res["summary"]

    @patch('app.agents.sentiment_agent.get_llm')
    @patch('app.agents.sentiment_agent.get_registry')
    @pytest.mark.anyio
    async def test_sentiment_agent(self, mock_registry, mock_get_llm, mock_llm_response):
        """Test SentimentAgent classifies text feeds."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm

        sent_tool = Mock()
        sent_tool.name = "analyze_news_sentiment"
        sent_tool.invoke.return_value = "Sentiment Index: POSITIVE"

        reg = Mock()
        reg.get.return_value = sent_tool
        mock_registry.return_value = reg

        agent = SentimentAgent()
        res = await agent.run(query="What is the sentiment?", context={"coin": "BTC", "raw_news": "1. \"Bitcoin rises\""})

        assert res["success"] is True
        assert res["evaluation"] == "Mocked LLM Expert Analysis Summary Content"

    @patch('app.agents.research_agent.get_llm')
    @patch('app.agents.research_agent.get_registry')
    @pytest.mark.anyio
    async def test_research_agent(self, mock_registry, mock_get_llm, mock_llm_response):
        """Test ResearchAgent queries RAG vector store."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm

        rag_tool = Mock()
        rag_tool.name = "search_knowledge_base"
        rag_tool.invoke.return_value = "Found: MACD Strategy guide details."

        reg = Mock()
        reg.get.return_value = rag_tool
        mock_registry.return_value = reg

        agent = ResearchAgent()
        res = await agent.run(query="strategy", context={"coin": "BTC"})

        assert res["success"] is True
        assert res["summary"] == "Mocked LLM Expert Analysis Summary Content"

    @patch('app.agents.risk_agent.get_llm')
    @patch('app.agents.risk_agent.get_registry')
    @pytest.mark.anyio
    async def test_risk_agent(self, mock_registry, mock_get_llm, mock_llm_response):
        """Test RiskAgent gets limits and sizing stops."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm

        bal_tool = Mock()
        bal_tool.name = "get_portfolio_balance"
        bal_tool.invoke.return_value = "USDT: 1000"

        risk_tool = Mock()
        risk_tool.name = "perform_risk_analysis"
        risk_tool.invoke.return_value = "SL: 44000 | TP: 48000"

        reg = Mock()
        reg.get.side_effect = lambda name: {
            "get_portfolio_balance": bal_tool,
            "perform_risk_analysis": risk_tool
        }[name]
        mock_registry.return_value = reg

        agent = RiskAgent()
        res = await agent.run(query="assess risk", context={"coin": "BTC", "recommended_signal": "BUY", "close_price": 45000.0})

        assert res["success"] is True
        assert res["analysis"] == "Mocked LLM Expert Analysis Summary Content"


class TestCryptoOrchestrator:
    """Integration tests for the LangGraph orchestrator state machine."""

    @patch('app.agents.orchestrator.MarketAgent')
    @patch('app.agents.orchestrator.NewsAgent')
    @patch('app.agents.orchestrator.SentimentAgent')
    @patch('app.agents.orchestrator.ResearchAgent')
    @patch('app.agents.orchestrator.RiskAgent')
    @patch('app.agents.orchestrator.ReportAgent')
    @patch('app.agents.orchestrator.get_llm')
    @pytest.mark.anyio
    async def test_orchestrator_full_run(
        self,
        mock_get_llm,
        mock_report_cls,
        mock_risk_cls,
        mock_research_cls,
        mock_sentiment_cls,
        mock_news_cls,
        mock_market_cls
    ):
        """Test orchestrator executes graph nodes in correct sequence."""
        # 1. Mock the parser LLM call (COIN: ETH, TIMEFRAME: 4H)
        mock_llm = Mock()
        mock_llm.invoke.return_value = AIMessage(content="COIN: ETH, TIMEFRAME: 4H")
        mock_get_llm.return_value = mock_llm

        # 2. Mock each agent instance run method
        mock_market = mock_market_cls.return_value
        mock_market.run = AsyncMock(return_value={
            "success": True,
            "analysis": "Market Trend: Bullish",
            "data": {
                "indicators_summary": "Close Price: $3000\nATR: 50\nConfluence Signal: BUY"
            }
        })

        mock_news = mock_news_cls.return_value
        mock_news.run = AsyncMock(return_value={
            "success": True,
            "summary": "News Summary: Positive updates",
            "data": {
                "raw_news": "1. Ethereum core upgrade successful"
            }
        })

        mock_sentiment = mock_sentiment_cls.return_value
        mock_sentiment.run = AsyncMock(return_value={
            "success": True,
            "evaluation": "Sentiment Analysis: Optimistic"
        })

        mock_research = mock_research_cls.return_value
        mock_research.run = AsyncMock(return_value={
            "success": True,
            "summary": "RAG insights: Strategy loaded"
        })

        mock_risk = mock_risk_cls.return_value
        mock_risk.run = AsyncMock(return_value={
            "success": True,
            "analysis": "Risk parameters: Safe limits"
        })

        mock_report = mock_report_cls.return_value
        mock_report.run = AsyncMock(return_value={
            "success": True,
            "report": "# ETH Thesis Investment Report\nFinal report summary."
        })

        # 3. Instantiate and run Orchestrator
        orchestrator = CryptoOrchestrator()
        report = await orchestrator.run_analysis(
            "Generate analysis for ETH on 4h timeframe",
            thread_id="test_thread"
        )

        assert "ETH Thesis Investment Report" in report
        assert "Final report summary." in report
        orchestrator.close()
