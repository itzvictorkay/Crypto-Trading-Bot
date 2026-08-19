"""
app/agents/market_agent.py
--------------------------
Specialized agent for market data and technical analysis.
Gathers price, volume, S/R levels, and calculates technical confluences.
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.llm_provider import get_llm
from app.tools import get_registry

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """Agent specialized in technical and market indicators analysis."""

    def __init__(self):
        # Fetch relevant tools from registry
        registry = get_registry()
        market_tools = [
            registry.get("get_crypto_price"),
            registry.get("get_market_data"),
            registry.get("get_volume_stats"),
            registry.get("get_support_resistance"),
            registry.get("calculate_market_indicators")
        ]
        super().__init__(
            name="MarketAgent",
            description="Analyzes market prices, volumes, support/resistance, and technical indicators.",
            tools=market_tools
        )
        self.llm = get_llm()

    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute market analysis.
        """
        coin = (context or {}).get("coin", "BTC")
        timeframe = (context or {}).get("timeframe", "1h")
        symbol = f"{coin}/USDT"
        
        logger.info(f"Running MarketAgent analysis for {symbol} [{timeframe}]")
        
        try:
            # 1. Fetch current price
            price_tool = next(t for t in self.tools if t.name == "get_crypto_price")
            price_str = price_tool.invoke({"symbol": symbol})
            
            # 2. Fetch support/resistance
            sr_tool = next(t for t in self.tools if t.name == "get_support_resistance")
            sr_str = sr_tool.invoke({"symbol": symbol})
            
            # 3. Fetch indicators summary
            ind_tool = next(t for t in self.tools if t.name == "calculate_market_indicators")
            ind_str = ind_tool.invoke({"symbol": symbol, "timeframe": timeframe})
            
            # 4. Synthesize via LLM
            prompt = (
                f"You are a Technical Analysis Expert. Review the raw data below for {symbol}:\n\n"
                f"--- Price Data ---\n{price_str}\n\n"
                f"--- Support & Resistance ---\n{sr_str}\n\n"
                f"--- Technical Indicators ---\n{ind_str}\n\n"
                f"Synthesize this data. Explain the trend bias, current confluence signal, and support/resistance levels. "
                f"Be objective, professional, and clear."
            )
            
            messages = [
                SystemMessage(content="You are a professional crypto technical analyst."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            from app.agents.base_agent import parse_llm_content
            analysis_text = parse_llm_content(response.content)
            
            return {
                "success": True,
                "analysis": analysis_text,
                "data": {
                    "price_summary": price_str,
                    "support_resistance": sr_str,
                    "indicators_summary": ind_str
                }
            }
            
        except Exception as e:
            logger.error(f"Error in MarketAgent: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
