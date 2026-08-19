"""
app/rag/retriever.py
--------------------
Orchestration layer for RAG (Retrieval-Augmented Generation).
Coordinates document ingestion via DocumentLoader and queries via VectorStoreManager.
Exposes a clean search API for agent tools.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import VectorStoreManager
from app.config_langchain import RAG_ENABLED

logger = logging.getLogger(__name__)


class RAGService:
    """Orchestrates loading, indexing, and retrieving documents for the AI agent."""

    def __init__(self, collection_name: str = "crypto_knowledge_base"):
        self.enabled = RAG_ENABLED
        self.vector_store = None
        self.collection_name = collection_name
        
        if self.enabled:
            try:
                self.vector_store = VectorStoreManager(collection_name=self.collection_name)
            except Exception as e:
                logger.error(f"Failed to initialize VectorStoreManager: {e}")
                self.enabled = False
        else:
            logger.info("RAG is disabled in configuration.")

    def ingest_directory(self, directory_path: str = "./data/documents") -> int:
        """
        Scan and ingest all documents in the target folder into the vector store.
        
        Args:
            directory_path: Absolute or relative directory path containing files
            
        Returns:
            int: Number of chunks successfully ingested
        """
        if not self.enabled or not self.vector_store:
            logger.warning("RAG is disabled or vector store is uninitialized. Skipping ingestion.")
            return 0
            
        try:
            logger.info(f"Starting directory ingestion from: {directory_path}")
            loader = DocumentLoader()
            chunks = loader.load_and_chunk_directory(directory_path)
            
            if not chunks:
                logger.info("No documents found to ingest.")
                return 0
                
            success = self.vector_store.add_documents(chunks)
            if success:
                logger.info(f"Ingestion complete. Added {len(chunks)} chunks.")
                return len(chunks)
            else:
                logger.error("Ingestion failed during ChromaDB upload.")
                return 0
        except Exception as e:
            logger.error(f"Error during RAG ingestion: {e}", exc_info=True)
            return 0

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base for text matching query.
        
        Args:
            query: Plain text search string
            limit: Maximum matches to retrieve
            
        Returns:
            List of matching chunk dicts with 'text', 'metadata', 'distance'
        """
        if not self.enabled or not self.vector_store:
            logger.info("RAG search requested but RAG is disabled.")
            return []
            
        if not query.strip():
            return []
            
        return self.vector_store.query(query, limit=limit)
        
    def get_status(self) -> Dict[str, Any]:
        """Retrieve vector store status (count, directory, enabled state)."""
        if not self.enabled or not self.vector_store:
            return {"enabled": False, "document_count": 0}
            
        info = self.vector_store.get_collection_info()
        info["enabled"] = True
        return info
