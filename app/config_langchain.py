"""
app/config_langchain.py
-----------------------
LangChain & AI configuration settings loaded from .env file.
Separate from main config.py to keep concerns isolated.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM Configuration ─────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()  # anthropic, openai, google

# ── Anthropic Claude ─────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "2048"))
CLAUDE_TEMPERATURE = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))

# ── OpenAI (optional, for future use) ──────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

# ── Google Gemini (already in use for trade signals) ───
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# ── LangChain Configuration ────────────────────
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "300"))  # 5 minutes

# ── RAG & Vector Database ─────────────────────
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "default")  # "default" uses Chroma's default

# ── Memory Configuration ──────────────────────
CONVERSATION_MEMORY_TYPE = os.getenv("CONVERSATION_MEMORY_TYPE", "buffer")  # buffer, summary, token_based
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
MEMORY_MAX_TOKENS = int(os.getenv("MEMORY_MAX_TOKENS", "4000"))

# ── News API Configuration ────────────────────
NEWS_API_ENABLED = os.getenv("NEWS_API_ENABLED", "true").lower() == "true"
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_KEY", "")  # From existing config

# ── API Rate Limiting ─────────────────────────
API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))

# ── Logging ───────────────────────────────────
LANGCHAIN_DEBUG = os.getenv("LANGCHAIN_DEBUG", "false").lower() == "true"
LOG_AGENT_DECISIONS = os.getenv("LOG_AGENT_DECISIONS", "true").lower() == "true"
LOG_TOOL_CALLS = os.getenv("LOG_TOOL_CALLS", "true").lower() == "true"
