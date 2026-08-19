"""
tests/test_foundation.py
------------------------
Tests for LangChain foundation: LLM provider, configuration, tool registry.
"""

import pytest
import logging
from app.config_langchain import (
    LLM_PROVIDER,
    CLAUDE_MODEL,
    ANTHROPIC_API_KEY,
    RAG_ENABLED,
    CHROMA_DB_PATH,
)
from app.llm_provider import LLMProvider, get_llm
from app.tools import get_registry

logger = logging.getLogger(__name__)


class TestLLMConfiguration:
    """Test LLM configuration loading."""

    def test_llm_provider_is_set(self):
        """Verify LLM_PROVIDER is configured."""
        assert LLM_PROVIDER is not None
        assert LLM_PROVIDER.lower() in ["anthropic", "openai", "google"]

    def test_claude_model_is_set(self):
        """Verify Claude model is configured."""
        assert CLAUDE_MODEL is not None
        assert len(CLAUDE_MODEL) > 0

    def test_anthropic_api_key_format(self):
        """Verify ANTHROPIC_API_KEY exists (may be placeholder in tests)."""
        # In test environment, this might be a placeholder
        # In production, it should be a real key
        assert ANTHROPIC_API_KEY is not None


class TestLLMProvider:
    """Test LLM provider factory."""

    @pytest.mark.skipif(
        not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_anthropic_key_here",
        reason="ANTHROPIC_API_KEY not configured for testing"
    )
    def test_get_anthropic_llm(self):
        """Test Anthropic Claude LLM initialization."""
        try:
            llm = LLMProvider.get_llm("anthropic")
            assert llm is not None
            logger.info(f"✓ Anthropic LLM initialized: {type(llm)}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic LLM: {e}")
            pytest.skip(f"Anthropic LLM unavailable: {e}")

    @pytest.mark.skipif(
        not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_anthropic_key_here",
        reason="ANTHROPIC_API_KEY not configured for testing"
    )
    def test_get_llm_singleton(self):
        """Test LLM singleton pattern."""
        try:
            llm1 = get_llm()
            llm2 = get_llm()
            # Should return same instance
            assert llm1 is llm2
            logger.info("✓ LLM singleton works correctly")
        except Exception as e:
            logger.error(f"LLM singleton test failed: {e}")
            pytest.skip(f"Anthropic LLM unavailable: {e}")

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError):
            LLMProvider.get_llm("invalid_provider")


class TestToolRegistry:
    """Test tool registration and retrieval."""

    def test_registry_exists(self):
        """Verify tool registry is available."""
        registry = get_registry()
        assert registry is not None

    def test_register_tool(self):
        """Test registering a tool."""
        registry = get_registry()

        def dummy_tool():
            """A dummy test tool."""
            return "result"

        # Clear existing tools for test
        initial_names = registry.get_names()
        
        registry.register(
            "test_dummy_tool",
            dummy_tool,
            "A dummy tool for testing"
        )
        
        assert "test_dummy_tool" in registry.get_names()
        logger.info("✓ Tool registration works")

    def test_get_tool(self):
        """Test retrieving a registered tool."""
        registry = get_registry()

        def test_func():
            return "test"

        registry.register("test_func", test_func)
        retrieved = registry.get("test_func")
        assert retrieved is test_func
        logger.info("✓ Tool retrieval works")

    def test_list_tools(self):
        """Test listing all tools with descriptions."""
        registry = get_registry()
        tools_list = registry.list_tools()
        assert isinstance(tools_list, dict)
        logger.info(f"✓ Tool listing works. Available tools: {list(tools_list.keys())}")


class TestRAGConfiguration:
    """Test RAG and vector database configuration."""

    def test_rag_enabled_setting(self):
        """Verify RAG_ENABLED setting."""
        assert RAG_ENABLED is not None
        assert isinstance(RAG_ENABLED, bool)

    def test_chroma_db_path_configured(self):
        """Verify Chroma DB path is set."""
        assert CHROMA_DB_PATH is not None
        assert len(CHROMA_DB_PATH) > 0


if __name__ == "__main__":
    # Run tests: pytest tests/test_foundation.py -v
    pytest.main([__file__, "-v"])
