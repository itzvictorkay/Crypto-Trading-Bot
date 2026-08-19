"""
app/agents/news_agent.py
------------------------
Specialized agent for retrieving news and articles.
Queries news aggregators and compiles relevant media timelines.
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.llm_provider import get_llm
from app.tools import get_registry

logger = logging.getLogger(__name__)


class NewsAgent(BaseAgent):
    """Agent specialized in collecting news headlines."""

    def __init__(self):
        registry = get_registry()
        news_tools = [
            registry.get("search_crypto_news")
        ]
        super().__init__(
            name="NewsAgent",
            description="Searches and retrieves the latest news headlines and articles for a cryptocurrency.",
            tools=news_tools
        )
        self.llm = get_llm()

    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute news retrieval and compilation.
        """
        coin = (context or {}).get("coin", "BTC")
        
        logger.info(f"Running NewsAgent analysis for {coin}")
        
        try:
            news_tool = next(t for t in self.tools if t.name == "search_crypto_news")
            news_str = news_tool.invoke({"symbol": coin, "limit": 10})
            
            # Format and summarize headlines via LLM
            prompt = (
                f"You are a Crypto News Editor. Review the raw news feed below for {coin}:\n\n"
                f"{news_str}\n\n"
                f"Summarize the key events, narratives, or announcements. "
                f"Highlight positive updates (e.g. upgrades, listings) and negative risks (e.g. hacks, regulations). "
                f"Keep it brief and structured."
            )
            
            messages = [
                SystemMessage(content="You are a professional financial news analyst."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            from app.agents.base_agent import parse_llm_content
            summary_text = parse_llm_content(response.content)
            
            return {
                "success": True,
                "summary": summary_text,
                "data": {
                    "raw_news": news_str
                }
            }
            
        except Exception as e:
            logger.error(f"Error in NewsAgent: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
