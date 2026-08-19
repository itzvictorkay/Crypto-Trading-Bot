"""
app/agents/base_agent.py
------------------------
Base class for all specialized agents.
Provides common functionality like logging, error handling, tool management.
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_llm_content(content) -> str:
    """Safely convert any LLM response content (str or list of blocks) to a string."""
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, str):
                parts.append(block)
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


class BaseAgent(ABC):
    """Base class for all crypto analysis agents."""

    def __init__(self, name: str, description: str, tools: Optional[List] = None):
        """
        Initialize base agent.

        Args:
            name: Agent name (e.g., "MarketAgent")
            description: Agent purpose description
            tools: List of LangChain tools available to this agent
        """
        self.name = name
        self.description = description
        self.tools = tools or []
        self.created_at = datetime.now()
        logger.info(f"Initialized {self.name}: {description}")

    @abstractmethod
    async def run(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the agent on a query.

        Args:
            query: User query or task description
            context: Optional context dict (previous results, etc.)

        Returns:
            Dict with agent response, reasoning, and any relevant data
        """
        pass

    def add_tool(self, tool):
        """Add a tool to this agent's toolkit."""
        self.tools.append(tool)
        logger.debug(f"{self.name} added tool: {tool.name if hasattr(tool, 'name') else tool}")

    def get_tools(self) -> List:
        """Get all tools available to this agent."""
        return self.tools

    def log_execution(self, query: str, result: Dict[str, Any], duration: float):
        """Log agent execution for debugging/monitoring."""
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logger.debug(
                f"{self.name} executed query in {duration:.2f}s: "
                f"Query='{query[:100]}...' Result={result}"
            )
