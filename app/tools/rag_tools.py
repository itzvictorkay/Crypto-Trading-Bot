"""
app/tools/rag_tools.py
----------------------
LangChain tools for Retrieval-Augmented Generation (RAG).
Allows the AI agent to search and update the local knowledge base.
"""

import logging
import os
from langchain_core.tools import tool

from app.rag.retriever import RAGService

logger = logging.getLogger(__name__)

# Module-level service instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get or create RAGService instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


@tool
def search_knowledge_base(query: str, limit: int = 5) -> str:
    """
    Search the local RAG knowledge base for research papers, strategies, and coin documentation.
    Use this to lookup trading rules, specific strategy details, or tokenomics info.
    
    Args:
        query: Specific search terms or question (e.g. 'what is the EMA crossover strategy?')
        limit: Number of search results to return (default 5)
        
    Returns:
        Structured search results string
    """
    try:
        service = get_rag_service()
        if not service.enabled:
            return "Knowledge base search is currently disabled in configuration."
            
        results = service.search(query, limit=limit)
        
        if not results:
            return f"No matching documents found in knowledge base for query: '{query}'."
            
        formatted_results = []
        for i, res in enumerate(results, 1):
            meta = res['metadata']
            source = meta.get('source_file', 'unknown')
            chunk_idx = meta.get('chunk_index', 0)
            tot_chunks = meta.get('total_chunks', 1)
            
            formatted_results.append(
                f"--- Result {i} (Source: {source} [Chunk {chunk_idx + 1}/{tot_chunks}]) (Distance: {res['distance']:.4f}) ---\n"
                f"{res['text']}"
            )
            
        header = f"=== Knowledge Base Search Results for: '{query}' ===\n\n"
        return header + "\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error in search_knowledge_base tool: {e}")
        return f"Error querying knowledge base: {str(e)}"


@tool
def ingest_knowledge_documents(directory_path: str = "./data/documents") -> str:
    """
    Scan a directory for new documents (TXT, MD, PDF, JSON) and parse/index them into the vector database.
    
    Args:
        directory_path: Absolute or relative directory path containing files (default './data/documents')
        
    Returns:
        Summary message of the ingestion results
    """
    try:
        service = get_rag_service()
        if not service.enabled:
            return "Knowledge base ingestion is disabled in configuration."
            
        if not os.path.exists(directory_path):
            return f"Error: The specified directory '{directory_path}' does not exist."
            
        chunk_count = service.ingest_directory(directory_path)
        
        # Get updated info
        info = service.get_status()
        
        return (
            f"=== Ingestion Results ===\n"
            f"Directory processed: {directory_path}\n"
            f"New chunks indexed: {chunk_count}\n"
            f"Total database size: {info.get('document_count', 0)} chunks"
        )
        
    except Exception as e:
        logger.error(f"Error in ingest_knowledge_documents tool: {e}")
        return f"Error during document ingestion: {str(e)}"


# Export tools for registration
RAG_TOOLS = [
    search_knowledge_base,
    ingest_knowledge_documents,
]
