"""
app/agents/orchestrator.py
--------------------------
Orchestrator agent for routing queries and coordinating sub-agents.
Builds the LangGraph state machine flow (Market -> News -> Sentiment -> Research -> Risk -> Report)
with thread-based persistent SQLite checkpointer memory.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from app.llm_provider import get_llm
from app.agents.market_agent import MarketAgent
from app.agents.news_agent import NewsAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.research_agent import ResearchAgent
from app.agents.risk_agent import RiskAgent
from app.agents.report_agent import ReportAgent

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """LangGraph agent state definition."""
    messages: Annotated[List[BaseMessage], add_messages]
    coin: str
    timeframe: str
    
    # Internal agent results cache
    market_analysis: Optional[str]
    news_analysis: Optional[str]
    sentiment_analysis: Optional[str]
    research_analysis: Optional[str]
    risk_analysis: Optional[str]
    
    # Final output
    final_report: Optional[str]
    close_price: Optional[float]
    atr: Optional[float]
    recommended_signal: Optional[str]


class CryptoOrchestrator:
    """Orchestrator that compiles reports via a LangGraph state machine."""

    def __init__(self):
        # 1. Initialize sub-agents
        self.market_agent = MarketAgent()
        self.news_agent = NewsAgent()
        self.sentiment_agent = SentimentAgent()
        self.research_agent = ResearchAgent()
        self.risk_agent = RiskAgent()
        self.report_agent = ReportAgent()
        self.llm = get_llm()
        
        # 2. Setup Memory checkpointer for conversational persistence
        logger.info("Initializing LangGraph MemorySaver checkpointer")
        self.checkpointer = MemorySaver()
        
        # 3. Assemble LangGraph Workflow
        self.workflow = self._build_workflow()
        self.graph = self.workflow.compile(checkpointer=self.checkpointer)
        logger.info("LangGraph orchestrator workflow compiled successfully")

    def _build_workflow(self) -> StateGraph:
        """Define nodes, edges, and compilation parameters."""
        builder = StateGraph(AgentState)
        
        # Define Nodes
        builder.add_node("parse_request", self._parse_request_node)
        builder.add_node("market_node", self._market_node)
        builder.add_node("news_node", self._news_node)
        builder.add_node("sentiment_node", self._sentiment_node)
        builder.add_node("research_node", self._research_node)
        builder.add_node("risk_node", self._risk_node)
        builder.add_node("report_node", self._report_node)
        
        # Define Edges
        builder.add_edge(START, "parse_request")
        builder.add_edge("parse_request", "market_node")
        builder.add_edge("market_node", "news_node")
        builder.add_edge("news_node", "sentiment_node")
        builder.add_edge("sentiment_node", "research_node")
        builder.add_edge("research_node", "risk_node")
        builder.add_edge("risk_node", "report_node")
        builder.add_edge("report_node", END)
        
        return builder

    # --- Node Functions ---

    def _parse_request_node(self, state: AgentState) -> Dict[str, Any]:
        """Node to extract target token and timeframe parameters from query."""
        last_message = state["messages"][-1].content
        
        # Call LLM to parse parameters
        prompt = (
            "Analyze this user query and extract: \n"
            "1. Target cryptocurrency coin symbol (e.g. BTC, ETH, SOL). Default to 'BTC' if none is found.\n"
            "2. Timeframe (e.g. 15m, 1h, 4h, 1d). Default to '1h' if none is found.\n\n"
            f"Query: \"{last_message}\"\n\n"
            "Return only in this format: COIN: <coin>, TIMEFRAME: <timeframe>"
        )
        
        try:
            res = self.llm.invoke([HumanMessage(content=prompt)])
            from app.agents.base_agent import parse_llm_content
            response_text = parse_llm_content(res.content).strip().upper()
            
            # Simple parsing
            coin = "BTC"
            timeframe = "1h"
            
            if "COIN:" in response_text:
                coin = response_text.split("COIN:")[1].split(",")[0].strip()
            if "TIMEFRAME:" in response_text:
                timeframe = response_text.split("TIMEFRAME:")[1].strip()
                
            logger.info(f"Parsed parameters: Coin={coin}, Timeframe={timeframe}")
            return {
                "coin": coin,
                "timeframe": timeframe
            }
        except Exception as e:
            logger.error(f"Error parsing request parameters: {e}")
            return {"coin": "BTC", "timeframe": "1h"}

    async def _market_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for executing technical market analysis."""
        res = await self.market_agent.run(
            query=state["messages"][-1].content,
            context={"coin": state["coin"], "timeframe": state["timeframe"]}
        )
        
        # Parse close_price and atr and confluence signal from indicators_summary if available
        close_price = 0.0
        atr = None
        recommended_signal = "HOLD"
        
        if res.get("success") and res.get("data"):
            summary = res["data"]["indicators_summary"]
            # Extract close price e.g. "Close Price: $45000.00"
            try:
                for line in summary.split('\n'):
                    if "Close Price:" in line:
                        close_price = float(line.split('$')[1].replace(',', '').strip())
                    elif "ATR" in line:
                        atr = float(line.split(':')[-1].strip())
                    elif "Confluence Signal:" in line:
                        recommended_signal = line.split(':')[-1].strip()
            except Exception as e:
                logger.warning(f"Could not parse indicators from summary: {e}")
                
        return {
            "market_analysis": res.get("analysis", "Technical analysis failed."),
            "close_price": close_price,
            "atr": atr,
            "recommended_signal": recommended_signal
        }

    async def _news_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for fetching coin headlines."""
        res = await self.news_agent.run(
            query=state["messages"][-1].content,
            context={"coin": state["coin"]}
        )
        return {
            "news_analysis": res.get("summary", "News compilation failed."),
            "raw_news_data": res.get("data", {}).get("raw_news", "")
        }

    async def _sentiment_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for evaluating crowd sentiment index."""
        # Get raw news from previous node
        raw_news = state.get("raw_news_data", "")
        res = await self.sentiment_agent.run(
            query=state["messages"][-1].content,
            context={"coin": state["coin"], "raw_news": raw_news}
        )
        return {
            "sentiment_analysis": res.get("evaluation", "Sentiment classification failed.")
        }

    async def _research_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for querying internal document database (RAG)."""
        last_message = state["messages"][-1].content
        res = await self.research_agent.run(
            query=last_message,
            context={"coin": state["coin"]}
        )
        return {
            "research_analysis": res.get("summary", "RAG query failed.")
        }

    async def _risk_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for running position sizing and ATR risk calculations."""
        res = await self.risk_agent.run(
            query=state["messages"][-1].content,
            context={
                "coin": state["coin"],
                "recommended_signal": state.get("recommended_signal", "HOLD"),
                "close_price": state.get("close_price", 0.0),
                "atr": state.get("atr")
            }
        )
        return {
            "risk_analysis": res.get("analysis", "Risk assessment failed.")
        }

    async def _report_node(self, state: AgentState) -> Dict[str, Any]:
        """Node for synthesizing final PDF/Markdown thesis report."""
        res = await self.report_agent.run(
            query=state["messages"][-1].content,
            context={
                "coin": state["coin"],
                "timeframe": state["timeframe"],
                "market_analysis": state.get("market_analysis", "N/A"),
                "news_analysis": state.get("news_analysis", "N/A"),
                "sentiment_analysis": state.get("sentiment_analysis", "N/A"),
                "research_analysis": state.get("research_analysis", "N/A"),
                "risk_analysis": state.get("risk_analysis", "N/A")
            }
        )
        report = res.get("report", "Report compilation failed.")
        
        # Save output as AIMessage
        return {
            "final_report": report,
            "messages": [AIMessage(content=report)]
        }

    # --- Public API ---

    async def run_analysis(self, query: str, thread_id: str = "default_user") -> str:
        """
        Run the complete multi-agent orchestrator state graph for a coin.
        
        Args:
            query: The user query string.
            thread_id: Thread identifier for checkpoint memory.
            
        Returns:
            The compiled markdown report string.
        """
        config_params = {"configurable": {"thread_id": thread_id}}
        
        # Set up state input
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "coin": "BTC",
            "timeframe": "1h",
            "market_analysis": None,
            "news_analysis": None,
            "sentiment_analysis": None,
            "research_analysis": None,
            "risk_analysis": None,
            "final_report": None,
            "close_price": 0.0,
            "atr": None,
            "recommended_signal": "HOLD"
        }
        
        logger.info(f"Starting multi-agent orchestrator analysis (Thread: {thread_id})")
        final_state = await self.graph.ainvoke(initial_state, config=config_params)
        
        return final_state.get("final_report", "Error compiling analysis report.")

    def close(self):
        """Clean connection handles."""
        pass
