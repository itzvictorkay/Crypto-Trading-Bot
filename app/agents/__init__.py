"""
app/agents/
-----------
LangChain agents for specialized cryptocurrency research tasks.

Agents:
- market_agent.py      : Analyzes market data & technical indicators
- news_agent.py        : Retrieves & analyzes cryptocurrency news
- research_agent.py    : Queries knowledge base (RAG)
- sentiment_agent.py   : Analyzes overall sentiment
- risk_agent.py        : Performs risk analysis
- report_agent.py      : Generates structured research reports
- orchestrator.py      : Routes queries to appropriate agents

Base class:
- base_agent.py        : Common agent functionality
"""

from app.agents.orchestrator import CryptoOrchestrator

__all__ = [
    "CryptoOrchestrator",
]

