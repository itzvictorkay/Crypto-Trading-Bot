"""
app/rag/embeddings.py
---------------------
Embedding model configuration for RAG knowledge base.
Wraps Chroma's default on-device MiniLM embeddings.
"""

import logging
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


def get_embedding_function():
    """
    Get the default embedding function (MiniLM-L6-v2 on-device via ONNX / Tokenizers).
    """
    try:
        # Chroma's default embedding function runs all-MiniLM-L6-v2 locally.
        logger.info("Initializing Chroma default embedding function (all-MiniLM-L6-v2)")
        return embedding_functions.DefaultEmbeddingFunction()
    except Exception as e:
        logger.error(f"Error initializing embedding function: {e}")
        # Return fallback embedding function
        raise e
