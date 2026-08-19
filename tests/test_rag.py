"""
tests/test_rag.py
-----------------
Unit and integration tests for RAG loader, vector database, and LangChain tools.
Uses Chroma's EphemeralClient and a mocked embedding function to run completely offline.
"""

import os
import shutil
import pytest
from unittest.mock import Mock, patch
import chromadb

from app.rag.document_loader import split_text, DocumentLoader
from app.rag.vector_store import VectorStoreManager
from app.rag.retriever import RAGService
from app.tools import rag_tools


class MockEmbeddingFunction:
    """Mock embedding function to avoid downloading models or network calls during testing."""
    def __call__(self, input: list) -> list:
        return [[0.1] * 384 for _ in input]

    def embed_query(self, input: list) -> list:
        return [[0.1] * 384 for _ in input]

    def name(self) -> str:
        return "default"

    @property
    def is_legacy(self) -> bool:
        return False


@pytest.fixture(autouse=True)
def mock_embeddings():
    """Autouse fixture to mock the embedding function globally in RAG tests."""
    with patch('app.rag.vector_store.get_embedding_function', return_value=MockEmbeddingFunction()), \
         patch('app.rag.embeddings.get_embedding_function', return_value=MockEmbeddingFunction()), \
         patch('chromadb.utils.embedding_functions.DefaultEmbeddingFunction', return_value=MockEmbeddingFunction()):
        yield


class TestDocumentLoader:
    """Tests for document loading and splitting logic."""

    def test_split_text_basic(self):
        """Test basic character splitting."""
        text = "Hello world! This is a simple test text that we want to chunk."
        chunks = split_text(text, chunk_size=30, chunk_overlap=10)
        
        assert len(chunks) > 1
        assert all(len(c) <= 30 for c in chunks)
        # Check that overlap is functional
        assert chunks[1].startswith(chunks[0][-10:])

    def test_split_text_by_paragraphs(self):
        """Test splitting respect paragraph boundaries where possible."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = split_text(text, chunk_size=15, chunk_overlap=0)
        
        assert len(chunks) == 4
        assert chunks[0] == "Paragraph one."
        assert chunks[1] == "Paragraph two."
        assert chunks[2] == "Paragraph three"


@pytest.fixture
def temp_documents_dir(tmp_path):
    """Create a temporary directory with test files."""
    d = tmp_path / "documents"
    d.mkdir()
    
    # 1. Text file
    txt_file = d / "doc1.txt"
    txt_file.write_text("BTC is a digital currency. It operates on a decentralized ledger.", encoding="utf-8")
    
    # 2. Markdown file
    md_file = d / "doc2.md"
    md_file.write_text("# Strategy Guide\nUse RSI indicators to identify reversal zones.", encoding="utf-8")
    
    # 3. JSON file
    json_file = d / "doc3.json"
    json_file.write_text('{"symbol": "ETH", "description": "Smart contract platform"}', encoding="utf-8")
    
    return str(d)


@pytest.fixture
def ephemeral_vector_store():
    """Create a VectorStoreManager connected to a fresh EphemeralClient."""
    # Patch PersistentClient to return a fresh EphemeralClient on every call
    with patch('chromadb.PersistentClient', side_effect=lambda *args, **kwargs: chromadb.EphemeralClient()):
        manager = VectorStoreManager(collection_name="test_collection")
        manager.clear_collection()
        yield manager


class TestVectorStoreManager:
    """Tests for ChromaDB interaction using ephemeral DB."""

    def test_add_and_query_documents(self, ephemeral_vector_store):
        """Test that chunks are successfully indexed and queried."""
        chunks = [
            {
                "text": "Bitcoin is digital gold.",
                "metadata": {"source_file": "bitcoin.txt", "chunk_index": 0}
            },
            {
                "text": "Ethereum is a decentralized computer.",
                "metadata": {"source_file": "ethereum.txt", "chunk_index": 0}
            }
        ]
        
        # Ingestion
        success = ephemeral_vector_store.add_documents(chunks)
        assert success is True
        
        # Metrics check
        info = ephemeral_vector_store.get_collection_info()
        assert info["document_count"] == 2
        
        # Exact query
        results = ephemeral_vector_store.query("digital gold", limit=1)
        assert len(results) == 1
        assert results[0]["text"] in ["Bitcoin is digital gold.", "Ethereum is a decentralized computer."]
        assert results[0]["metadata"]["source_file"] in ["bitcoin.txt", "ethereum.txt"]

    def test_clear_collection(self, ephemeral_vector_store):
        """Test clearing all elements in vector store."""
        chunks = [{"text": "data", "metadata": {"source_file": "x.txt", "chunk_index": 0}}]
        ephemeral_vector_store.add_documents(chunks)
        
        assert ephemeral_vector_store.get_collection_info()["document_count"] == 1
        ephemeral_vector_store.clear_collection()
        assert ephemeral_vector_store.get_collection_info()["document_count"] == 0


class TestRAGService:
    """Integration tests for RAGService coordination."""

    def test_ingest_and_search_workflow(self, temp_documents_dir):
        """Test complete directory ingestion and search workflow."""
        with patch('chromadb.PersistentClient', return_value=chromadb.EphemeralClient()):
            service = RAGService(collection_name="test_rag_service")
            
            # Ingestion count
            count = service.ingest_directory(temp_documents_dir)
            assert count == 3  # 1 txt, 1 md, 1 json
            
            # Query
            hits = service.search("digital currency")
            assert len(hits) >= 1
            assert "BTC" in hits[0]["text"]
            assert hits[0]["metadata"]["source_file"] == "doc1.txt"


class TestRAGTools:
    """Tests for LangChain RAG tools."""

    @patch('app.tools.rag_tools.get_rag_service')
    def test_search_knowledge_base_tool(self, mock_get_service):
        """Test search_knowledge_base tool output styling."""
        mock_service = Mock()
        mock_service.enabled = True
        mock_service.search.return_value = [
            {
                "text": "RSI crossover is a dynamic trading strategy.",
                "metadata": {"source_file": "strategies.md", "chunk_index": 0, "total_chunks": 1},
                "distance": 0.1234
            }
        ]
        mock_get_service.return_value = mock_service

        result = rag_tools.search_knowledge_base.invoke({
            "query": "RSI strategy",
            "limit": 3
        })

        assert "strategies.md" in result
        assert "Result 1" in result
        assert "crossover is a dynamic" in result
        mock_service.search.assert_called_once_with("RSI strategy", limit=3)

    @patch('app.tools.rag_tools.get_rag_service')
    def test_ingest_knowledge_documents_tool(self, mock_get_service):
        """Test ingest_knowledge_documents tool output styling."""
        mock_service = Mock()
        mock_service.enabled = True
        mock_service.ingest_directory.return_value = 5
        mock_service.get_status.return_value = {"document_count": 12}
        mock_get_service.return_value = mock_service

        with patch('os.path.exists', return_value=True):
            result = rag_tools.ingest_knowledge_documents.invoke({
                "directory_path": "./data/docs_test"
            })

            assert "New chunks indexed: 5" in result
            assert "Total database size: 12 chunks" in result
            mock_service.ingest_directory.assert_called_once_with("./data/docs_test")


class TestRAGToolsIntegration:
    """Integration tests for tool schema and registry."""

    def test_tools_are_structured_tools(self):
        """Test that RAG tools are LangChain StructuredTool instances."""
        from langchain_core.tools import StructuredTool
        
        assert isinstance(rag_tools.search_knowledge_base, StructuredTool)
        assert isinstance(rag_tools.ingest_knowledge_documents, StructuredTool)

    def test_tools_registered_in_registry(self):
        """Test that RAG tools are successfully in the central registry."""
        from app.tools import get_registry
        
        registry = get_registry()
        assert "search_knowledge_base" in registry.get_names()
        assert "ingest_knowledge_documents" in registry.get_names()
