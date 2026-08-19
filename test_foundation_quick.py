"""
Quick foundation test script.
Run this to verify LangChain setup works correctly.

Usage:
    python test_foundation_quick.py
"""

import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required imports work."""
    logger.info("=" * 60)
    logger.info("Testing Python Imports")
    logger.info("=" * 60)
    
    try:
        import langchain_core
        logger.info("✓ langchain-core imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import langchain-core: {e}")
        logger.info("  Install with: pip install langchain-core")
        return False

    try:
        import langchain_anthropic
        logger.info("✓ langchain-anthropic imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import langchain-anthropic: {e}")
        logger.info("  Install with: pip install langchain-anthropic")
        return False

    try:
        import langgraph
        logger.info("✓ langgraph imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import langgraph: {e}")
        logger.info("  Install with: pip install langgraph")
        return False

    try:
        import chromadb
        logger.info("✓ chromadb imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import chromadb: {e}")
        logger.info("  Install with: pip install chromadb")
        return False

    logger.info("✓ All imports successful!\n")
    return True


def test_configuration():
    """Test configuration loading."""
    logger.info("=" * 60)
    logger.info("Testing Configuration")
    logger.info("=" * 60)
    
    try:
        from app.config_langchain import (
            LLM_PROVIDER,
            CLAUDE_MODEL,
            ANTHROPIC_API_KEY,
            RAG_ENABLED,
            CHROMA_DB_PATH,
        )
        
        logger.info(f"  LLM_PROVIDER: {LLM_PROVIDER}")
        logger.info(f"  CLAUDE_MODEL: {CLAUDE_MODEL}")
        logger.info(f"  RAG_ENABLED: {RAG_ENABLED}")
        logger.info(f"  CHROMA_DB_PATH: {CHROMA_DB_PATH}")
        
        if not ANTHROPIC_API_KEY:
            logger.warning("  ANTHROPIC_API_KEY not set - AI features will not work")
            logger.info("  Add ANTHROPIC_API_KEY to .env file")
        else:
            logger.info(f"  ANTHROPIC_API_KEY: {ANTHROPIC_API_KEY[:10]}...")
        
        logger.info("✓ Configuration loaded successfully!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}\n")
        return False


def test_llm_provider():
    """Test LLM provider initialization."""
    logger.info("=" * 60)
    logger.info("Testing LLM Provider")
    logger.info("=" * 60)
    
    try:
        from app.config_langchain import ANTHROPIC_API_KEY
        
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your_anthropic_key_here":
            logger.warning("  ANTHROPIC_API_KEY not configured")
            logger.info("  Skipping LLM provider initialization test")
            logger.info("  To enable: set ANTHROPIC_API_KEY in .env file\n")
            return True
        
        from app.llm_provider import LLMProvider
        
        logger.info("  Initializing Claude LLM...")
        llm = LLMProvider.get_llm("anthropic")
        logger.info(f"  LLM type: {type(llm).__name__}")
        logger.info("✓ LLM Provider initialized successfully!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ LLM Provider test failed: {e}\n")
        return False


def test_tool_registry():
    """Test tool registry."""
    logger.info("=" * 60)
    logger.info("Testing Tool Registry")
    logger.info("=" * 60)
    
    try:
        from app.tools import get_registry
        
        registry = get_registry()
        logger.info(f"  Registry type: {type(registry).__name__}")
        logger.info(f"  Currently registered tools: {len(registry.get_names())}")
        
        # Test registration
        def test_tool():
            """Test tool."""
            return "test"
        
        registry.register("test_tool", test_tool, "A test tool")
        logger.info(f"  After registration: {len(registry.get_names())} tools")
        
        logger.info("✓ Tool Registry working correctly!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Tool Registry test failed: {e}\n")
        return False


def test_directory_structure():
    """Test required directories exist."""
    logger.info("=" * 60)
    logger.info("Testing Directory Structure")
    logger.info("=" * 60)
    
    required_dirs = [
        "app/agents",
        "app/tools",
        "app/services",
        "app/rag",
        "app/memory",
        "app/reports",
        "app/api",
        "data/documents",
        "tests",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists():
            logger.info(f"  ✓ {dir_path}/")
        else:
            logger.warning(f"  ✗ {dir_path}/ (missing)")
            all_exist = False
    
    if all_exist:
        logger.info("✓ All required directories exist!\n")
    else:
        logger.warning("✗ Some directories are missing\n")
    
    return all_exist


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("LANGCHAIN FOUNDATION TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Configuration": test_configuration(),
        "Directory Structure": test_directory_structure(),
        "Tool Registry": test_tool_registry(),
        "LLM Provider": test_llm_provider(),
    }
    
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"SUMMARY: {passed}/{total} tests passed")
    logger.info("=" * 60 + "\n")
    
    if passed == total:
        logger.info("🎉 All foundation tests passed! Ready for Phase 3.")
        return 0
    else:
        logger.warning("⚠️  Some tests failed. See above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
