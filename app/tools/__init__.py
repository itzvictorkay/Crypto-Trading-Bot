"""
app/tools/
----------
LangChain tools registry and management.

Supported tools:
- market_tools.py        : Price, OHLCV, volume, market data
- technical_tools.py     : RSI, MACD, EMA, Bollinger Bands, etc.
- sentiment_tools.py     : News sentiment analysis
- news_tools.py          : Crypto news retrieval
- research_tools.py      : RAG knowledge base queries

Each tool follows LangChain's @tool decorator pattern.
"""

import logging
from typing import Dict, Callable, Any, List

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available LangChain tools."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, str] = {}

    def register(self, name: str, tool: Callable, description: str = ""):
        """
        Register a new tool.

        Args:
            name: Tool identifier (e.g., "get_crypto_price")
            tool: Callable tool function with @tool decorator
            description: Human-readable tool description
        """
        self._tools[name] = tool
        self._tool_descriptions[name] = description or getattr(tool, "__doc__", "")
        logger.debug(f"Registered tool: {name}")

    def get(self, name: str) -> Callable:
        """Get a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]

    def get_all(self) -> List[Callable]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_names(self) -> List[str]:
        """Get all tool names."""
        return list(self._tools.keys())

    def list_tools(self) -> Dict[str, str]:
        """Get tool names with descriptions."""
        return self._tool_descriptions.copy()


# Global registry instance
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry


def register_tool(name: str, tool: Callable, description: str = ""):
    """Convenience function to register a tool."""
    _registry.register(name, tool, description)


# ===========================
# Initialize Market Tools
# ===========================

try:
    from app.tools.market_tools import (
        get_crypto_price,
        get_market_data,
        get_volume_stats,
        get_price_comparison,
        get_price_change,
        get_support_resistance,
    )
    
    # Register market tools
    register_tool(
        "get_crypto_price",
        get_crypto_price,
        "Get current price of a cryptocurrency symbol"
    )
    register_tool(
        "get_market_data",
        get_market_data,
        "Get OHLCV historical data for a trading pair"
    )
    register_tool(
        "get_volume_stats",
        get_volume_stats,
        "Get volume statistics (average, max, min) for a symbol"
    )
    register_tool(
        "get_price_comparison",
        get_price_comparison,
        "Compare current prices across multiple cryptocurrency symbols"
    )
    register_tool(
        "get_price_change",
        get_price_change,
        "Calculate price change over a specified period (in percent)"
    )
    register_tool(
        "get_support_resistance",
        get_support_resistance,
        "Identify support and resistance levels for a trading pair"
    )
    
    logger.info("✓ Market tools registered (6 tools)")
    
except Exception as e:
    logger.warning(f"Failed to load market tools: {e}")

# ===========================
# Initialize Technical Tools
# ===========================

try:
    from app.tools.technical_tools import (
        calculate_rsi,
        calculate_macd,
        calculate_moving_averages,
        calculate_bollinger_bands,
        calculate_market_indicators,
    )
    
    register_tool(
        "calculate_rsi",
        calculate_rsi,
        "Calculate Relative Strength Index (RSI) for a trading pair"
    )
    register_tool(
        "calculate_macd",
        calculate_macd,
        "Calculate MACD lines and crossovers for a trading pair"
    )
    register_tool(
        "calculate_moving_averages",
        calculate_moving_averages,
        "Calculate EMAs and crossovers for trend direction"
    )
    register_tool(
        "calculate_bollinger_bands",
        calculate_bollinger_bands,
        "Calculate Bollinger Bands levels for volatility/range"
    )
    register_tool(
        "calculate_market_indicators",
        calculate_market_indicators,
        "Calculate comprehensive summary of all indicators (RSI, MACD, BB, ATR)"
    )
    
    logger.info("✓ Technical tools registered (5 tools)")
    
except Exception as e:
    logger.warning(f"Failed to load technical tools: {e}")

# ===========================
# Initialize Sentiment Tools
# ===========================

try:
    from app.tools.sentiment_tools import (
        analyze_news_sentiment,
    )
    
    register_tool(
        "analyze_news_sentiment",
        analyze_news_sentiment,
        "Analyze market sentiment of a list of news headlines for a specific coin"
    )
    
    logger.info("✓ Sentiment tools registered (1 tool)")
    
except Exception as e:
    logger.warning(f"Failed to load sentiment tools: {e}")

# ===========================
# Initialize News Tools
# ===========================

try:
    from app.tools.news_tools import (
        search_crypto_news,
    )
    
    register_tool(
        "search_crypto_news",
        search_crypto_news,
        "Search and retrieve recent news articles and headlines for a cryptocurrency"
    )
    
    logger.info("✓ News tools registered (1 tool)")
    
except Exception as e:
    logger.warning(f"Failed to load news tools: {e}")

# ===========================
# Initialize Risk Tools
# ===========================

try:
    from app.tools.risk_tools import (
        perform_risk_analysis,
        get_portfolio_balance,
    )
    
    register_tool(
        "perform_risk_analysis",
        perform_risk_analysis,
        "Calculate position sizing and Stop-Loss/Take-Profit levels for a symbol"
    )
    register_tool(
        "get_portfolio_balance",
        get_portfolio_balance,
        "Get current portfolio balance summary including risk limits"
    )
    
    logger.info("✓ Risk tools registered (2 tools)")
    
except Exception as e:
    logger.warning(f"Failed to load risk tools: {e}")

# ===========================
# Initialize RAG Tools
# ===========================

try:
    from app.tools.rag_tools import (
        search_knowledge_base,
        ingest_knowledge_documents,
    )
    
    register_tool(
        "search_knowledge_base",
        search_knowledge_base,
        "Search local RAG knowledge base for research papers, strategy guides, and token details"
    )
    register_tool(
        "ingest_knowledge_documents",
        ingest_knowledge_documents,
        "Ingest documents from a folder into the vector knowledge base"
    )
    
    logger.info("✓ RAG tools registered (2 tools)")
    
except Exception as e:
    logger.warning(f"Failed to load RAG tools: {e}")





