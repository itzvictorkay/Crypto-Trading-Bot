"""
app/agents/sentiment_agent.py
-----------------------------
Specialized agent for sentiment analysis.
Classifies news summaries and headlines into sentiment indexes (Positive/Negative/Neutral).
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.llm_provider import get_llm
from app.tools import get_registry

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """Agent specialized in market sentiment assessment."""

    def __init__(self):
        registry = get_registry()
        sentiment_tools = [
            registry.get("analyze_news_sentiment")
        ]
        super().__init__(
            name="SentimentAgent",
            description="Analyzes and quantifies crowd and media sentiment for a cryptocurrency.",
            tools=sentiment_tools
        )
        self.llm = get_llm()

    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute sentiment classification.
        """
        coin = (context or {}).get("coin", "BTC")
        raw_news = (context or {}).get("raw_news", "")
        
        logger.info(f"Running SentimentAgent analysis for {coin}")
        
        try:
            # We need raw headlines to feed to the sentiment tool
            # Extract headlines or pass them from context
            headlines_input = ""
            if raw_news:
                # Simple extraction of titles from the raw news tools string output
                # Let's extract lines that start with numbers (e.g. 1. "title")
                headlines = []
                for line in raw_news.split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit() and '"' in line:
                        # Extract title between quotes
                        try:
                            title = line.split('"')[1]
                            headlines.append(title)
                        except Exception:
                            pass
                headlines_input = "; ".join(headlines)
                
            if not headlines_input:
                headlines_input = f"{coin} price action continues; general crypto market updates"
                
            sentiment_tool = next(t for t in self.tools if t.name == "analyze_news_sentiment")
            sentiment_str = sentiment_tool.invoke({"coin": coin, "headlines": headlines_input})
            
            # Synthesize via LLM
            prompt = (
                f"You are a Crowd Sentiment Specialist. Review the sentiment tool output below for {coin}:\n\n"
                f"{sentiment_str}\n\n"
                f"Provide a brief evaluation of the sentiment. Discuss how it might affect short-term retail and institutional behavior."
            )
            
            messages = [
                SystemMessage(content="You are a professional sentiment and behavior analyst."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            from app.agents.base_agent import parse_llm_content
            evaluation = parse_llm_content(response.content)
            
            return {
                "success": True,
                "evaluation": evaluation,
                "data": {
                    "sentiment_report": sentiment_str
                }
            }
            
        except Exception as e:
            logger.error(f"Error in SentimentAgent: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
