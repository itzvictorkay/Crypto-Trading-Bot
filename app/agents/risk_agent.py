"""
app/agents/risk_agent.py
------------------------
Specialized agent for calculating trade risk parameters.
Determines safe sizing, Stop-Loss (SL), and Take-Profit (TP) parameters.
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.llm_provider import get_llm
from app.tools import get_registry

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Agent specialized in calculating trade sizing and risk constraints."""

    def __init__(self):
        registry = get_registry()
        risk_tools = [
            registry.get("perform_risk_analysis"),
            registry.get("get_portfolio_balance")
        ]
        super().__init__(
            name="RiskAgent",
            description="Performs risk assessments, capital sizing, and stops calculations.",
            tools=risk_tools
        )
        self.llm = get_llm()

    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute risk assessments.
        """
        coin = (context or {}).get("coin", "BTC")
        recommended_signal = (context or {}).get("recommended_signal", "HOLD")
        
        # Extract closing price and ATR if available in context
        close_price = (context or {}).get("close_price", 0.0)
        atr = (context or {}).get("atr", None)
        
        symbol = f"{coin}/USDT"
        
        logger.info(f"Running RiskAgent analysis for {symbol} Close={close_price} ATR={atr}")
        
        try:
            # 1. Fetch balance summary
            bal_tool = next(t for t in self.tools if t.name == "get_portfolio_balance")
            bal_str = bal_tool.invoke({})
            
            # If recommended signal is HOLD, we run a hypothetical BUY to give sizing info
            eval_signal = recommended_signal if recommended_signal in ["BUY", "SELL"] else "BUY"
            
            # If close price is 0, fetch current price or use a fallback
            if close_price <= 0.0:
                # Fallback: get current price from market service
                registry = get_registry()
                price_tool = registry.get("get_crypto_price")
                try:
                    price_res = price_tool.invoke({"symbol": symbol})
                    # Parse price float from e.g. "BTC/USDT Current Price: $45000.00"
                    close_price = float(price_res.split('$')[1].replace(',', ''))
                except Exception:
                    close_price = 1000.0 # Fallback
            
            # 2. Run risk assessment
            risk_tool = next(t for t in self.tools if t.name == "perform_risk_analysis")
            risk_str = risk_tool.invoke({
                "symbol": symbol,
                "current_price": close_price,
                "signal": eval_signal,
                "atr": atr
            })
            
            # Synthesize via LLM
            prompt = (
                f"You are a Risk Manager. Review the raw sizing and balance data below for {symbol}:\n\n"
                f"--- Balance Details ---\n{bal_str}\n\n"
                f"--- Hypothetical/Proposed Trade Sizing ({eval_signal}) ---\n{risk_str}\n\n"
                f"Analyze the risk parameters. Explain the recommended entry sizing, stop-loss and take-profit targets, "
                f"and verify if the trade is safe according to portfolio limits."
            )
            
            messages = [
                SystemMessage(content="You are a professional risk officer."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            from app.agents.base_agent import parse_llm_content
            analysis = parse_llm_content(response.content)
            
            return {
                "success": True,
                "analysis": analysis,
                "data": {
                    "balance_summary": bal_str,
                    "risk_analysis": risk_str
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RiskAgent: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
