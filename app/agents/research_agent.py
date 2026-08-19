"""
app/agents/research_agent.py
----------------------------
Specialized agent for retrieving domain knowledge.
Queries the local ChromaDB vector store (RAG) for strategies and documents.
"""

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.llm_provider import get_llm
from app.tools import get_registry

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Agent specialized in querying RAG knowledge base."""

    def __init__(self):
        registry = get_registry()
        research_tools = [
            registry.get("search_knowledge_base")
        ]
        super().__init__(
            name="ResearchAgent",
            description="Queries local knowledge base (RAG) for research papers and strategies.",
            tools=research_tools
        )
        self.llm = get_llm()

    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute RAG document retrieval.
        """
        coin = (context or {}).get("coin", "BTC")
        user_query = query
        
        logger.info(f"Running ResearchAgent search for '{user_query}' [{coin}]")
        
        try:
            rag_tool = next(t for t in self.tools if t.name == "search_knowledge_base")
            # Build search query combining coin and user query
            search_query = f"{coin} {user_query}"
            rag_str = rag_tool.invoke({"query": search_query, "limit": 3})
            
            # Synthesize search hits
            prompt = (
                f"You are a Research Assistant. Review the RAG search hits below for '{search_query}':\n\n"
                f"{rag_str}\n\n"
                f"Summarize the relevant insights, strategies, or background info found in the database. "
                f"If no matching documents are found, summarize general knowledge about the tokenomics or features of {coin}."
            )
            
            messages = [
                SystemMessage(content="You are a meticulous researcher."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            from app.agents.base_agent import parse_llm_content
            research_summary = parse_llm_content(response.content)
            
            return {
                "success": True,
                "summary": research_summary,
                "data": {
                    "raw_research": rag_str
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ResearchAgent: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
