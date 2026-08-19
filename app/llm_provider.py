"""
app/llm_provider.py
-------------------
LLM provider factory for flexible model selection.
Currently configured for Anthropic Claude 3.5 Sonnet.
Can be extended for OpenAI, Google, or other providers.
"""

import logging
from typing import Optional
from app.config_langchain import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    CLAUDE_MAX_TOKENS,
    CLAUDE_TEMPERATURE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
)

logger = logging.getLogger(__name__)


class LLMProvider:
    """Factory for creating LLM instances based on configuration."""

    @staticmethod
    def get_llm(provider: Optional[str] = None):
        """
        Get LLM instance based on provider configuration.
        
        Args:
            provider: LLM provider name ('anthropic', 'openai', 'google')
                     If None, uses LLM_PROVIDER from config
        
        Returns:
            Instantiated LLM object ready for LangChain
        
        Raises:
            ValueError: If provider not configured or API key missing
        """
        provider = provider or LLM_PROVIDER

        if provider.lower() == "anthropic":
            return LLMProvider._get_anthropic_llm()
        elif provider.lower() == "openai":
            return LLMProvider._get_openai_llm()
        elif provider.lower() == "google":
            return LLMProvider._get_google_llm()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _get_anthropic_llm():
        """Initialize Anthropic Claude LLM."""
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not set in .env. "
                "Cannot initialize Claude LLM."
            )

        try:
            from langchain_anthropic import ChatAnthropic

            logger.info(
                f"Initializing Claude LLM: {CLAUDE_MODEL} "
                f"(max_tokens={CLAUDE_MAX_TOKENS}, temperature={CLAUDE_TEMPERATURE})"
            )

            return ChatAnthropic(
                model=CLAUDE_MODEL,
                api_key=ANTHROPIC_API_KEY,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE,
            )
        except ImportError:
            raise ImportError(
                "langchain-anthropic not installed. "
                "Install: pip install langchain-anthropic"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Claude LLM: {e}")
            raise

    @staticmethod
    def _get_openai_llm():
        """Initialize OpenAI LLM (for future use)."""
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not set in .env. "
                "Cannot initialize OpenAI LLM."
            )

        try:
            from langchain_openai import ChatOpenAI

            logger.info(f"Initializing OpenAI LLM: {OPENAI_MODEL}")

            return ChatOpenAI(
                model=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
            )
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. "
                "Install: pip install langchain-openai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}")
            raise

    @staticmethod
    def _get_google_llm():
        """Initialize Google Gemini LLM (for future use)."""
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not set in .env. "
                "Cannot initialize Google LLM."
            )

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            logger.info(f"Initializing Google Gemini LLM: {GEMINI_MODEL}")

            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                api_key=GOOGLE_API_KEY,
            )
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install: pip install langchain-google-genai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google LLM: {e}")
            raise


# Singleton instance for convenient access
_llm_instance = None


def get_llm():
    """Get or create the default LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMProvider.get_llm()
    return _llm_instance
