"""
app/
----
Crypto AI Research & Analysis Agent built with LangChain.

Modular structure:
- agents/      : AI agents (market, news, research, risk, report, orchestrator)
- tools/       : LangChain tools for agent use
- services/    : Business logic services (market, technical, sentiment, news, risk)
- rag/         : Retrieval-augmented generation (vector DB, document handling)
- memory/      : Conversation memory management
- reports/     : Report generation & formatting
- api/         : FastAPI routes
- config_langchain.py  : LLM & LangChain configuration
- llm_provider.py      : LLM factory (Anthropic Claude)
"""
