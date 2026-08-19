"""
app/agents/report_agent.py
--------------------------
Specialized agent for drafting research reports.
Synthesizes inputs from Market, News, Sentiment, Research, and Risk agents.
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.llm_provider import get_llm

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Agent specialized in writing comprehensive crypto research reports."""

    def __init__(self):
        super().__init__(
            name="ReportAgent",
            description="Compiles and formats structured cryptocurrency analysis reports."
        )
        self.llm = get_llm()

    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synthesize report from context.
        """
        coin = (context or {}).get("coin", "BTC")
        timeframe = (context or {}).get("timeframe", "1h")
        
        market_analysis = (context or {}).get("market_analysis", "N/A")
        news_analysis = (context or {}).get("news_analysis", "N/A")
        sentiment_analysis = (context or {}).get("sentiment_analysis", "N/A")
        research_analysis = (context or {}).get("research_analysis", "N/A")
        risk_analysis = (context or {}).get("risk_analysis", "N/A")
        
        logger.info(f"Running ReportAgent generation for {coin}")
        
        prompt = (
            f"You are a Senior Crypto Investment Analyst. Compile a professional, detailed Research and Analysis Report for {coin} [{timeframe}].\n\n"
            f"Synthesize the outputs from our specialized analysts below:\n\n"
            f"### 1. TECHNICAL ANALYSIS (Trend, Indicators, Support/Resistance):\n{market_analysis}\n\n"
            f"### 2. NEWS SUMMARY:\n{news_analysis}\n\n"
            f"### 3. SENTIMENT ASSESSMENT:\n{sentiment_analysis}\n\n"
            f"### 4. DOMAIN KNOWLEDGE & RETRIEVED STRATEGIES:\n{research_analysis}\n\n"
            f"### 5. CAPITAL SIZING & RISK PROFILES:\n{risk_analysis}\n\n"
            f"Compile a structured report in Markdown. It must include:\n"
            f"- Executive Summary (Thesis & recommended Confluence direction: BUY, SELL, or HOLD)\n"
            f"- Technical Indicators & Levels Section\n"
            f"- Market News & Sentiment Analysis\n"
            f"- Risk Management & Position Sizing Section\n"
            f"- Conclusion / Next Steps"
        )
        
        try:
            messages = [
                SystemMessage(content="You are a professional investment report writer."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            from app.agents.base_agent import parse_llm_content
            report_text = parse_llm_content(response.content)
            
            return {
                "success": True,
                "report": report_text
            }
        except Exception as e:
            logger.error(f"Error in ReportAgent: {e}")
            return {
                "success": False,
                "error": str(e)
            }
