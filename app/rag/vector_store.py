"""
app/rag/vector_store.py
---------------------
Vector database manager using ChromaDB.
Handles document ingestion, persistent storage, and metadata filtering.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb

from app.config_langchain import CHROMA_DB_PATH
from app.rag.embeddings import get_embedding_function

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages local Chroma vector database operations."""

    def __init__(self, collection_name: str = "crypto_knowledge_base"):
        """
        Initialize Chroma PersistentClient and load target collection.
        """
        self.db_path = CHROMA_DB_PATH
        # Ensure database directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        logger.info(f"Connecting to ChromaDB at: {self.db_path}")
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection_name = collection_name
        self.embedding_function = get_embedding_function()
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
        logger.info(f"Loaded Chroma collection: '{self.collection_name}'")

    def add_documents(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add or update chunk documents in the vector collection.
        
        Args:
            chunks: List of parsed chunk dicts with 'text' and 'metadata'
            
        Returns:
            bool: Success status
        """
        if not chunks:
            logger.info("No document chunks to add to vector store.")
            return True
            
        try:
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                documents.append(chunk["text"])
                metadatas.append(chunk["metadata"])
                
                # Generate unique ID based on file and chunk index
                source_file = chunk["metadata"].get("source_file", "unknown")
                chunk_idx = chunk["metadata"].get("chunk_index", 0)
                # Replace special characters to clean IDs
                clean_file = source_file.replace(" ", "_").replace("/", "_").replace("\\", "_")
                ids.append(f"{clean_file}_chunk_{chunk_idx}")
                
            logger.info(f"Upserting {len(documents)} chunks to '{self.collection_name}' collection")
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}", exc_info=True)
            return False

    def query(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query vector collection for similar text documents.
        
        Args:
            query_text: Plain text search query
            limit: Maximum results to return
            
        Returns:
            List of matching records with text, metadata, and distance scores
        """
        try:
            logger.info(f"Querying vector store: '{query_text}' (limit: {limit})")
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit
            )
            
            formatted_results = []
            
            # Chroma returns lists of lists for documents, metadatas, distances
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                ids = results["ids"][0] if results.get("ids") else [""] * len(docs)
                distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
                
                for doc, meta, doc_id, dist in zip(docs, metas, ids, distances):
                    formatted_results.append({
                        "text": doc,
                        "metadata": meta,
                        "id": doc_id,
                        "distance": dist
                    })
                    
            logger.info(f"Found {len(formatted_results)} matches in vector store")
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metrics (e.g. document counts)."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "db_path": self.db_path
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
            
    def clear_collection(self) -> bool:
        """Delete all documents in the collection."""
        try:
            # Recreate collection to wipe it completely
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Cleared Chroma collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error clearing Chroma collection: {e}")
            return False
