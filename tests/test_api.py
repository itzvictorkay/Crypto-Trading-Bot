"""
tests/test_api.py
------------------
Integration tests for FastAPI dashboard endpoints.
Mocks the orchestrator and database layers to execute offline.
"""

import pytest
import os
import io
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from dashboard.dashboard_app import app, authenticate, db

# Override authentication dependency for tests
app.dependency_overrides[authenticate] = lambda: "admin"


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    # Use an ephemeral in-memory database for testing
    with patch('dashboard.shared_db.sqlite3') as mock_sqlite:
        yield TestClient(app)


class TestDashboardAPI:
    """Tests for dashboard FastAPI endpoints."""

    @patch('dashboard.dashboard_app.db')
    def test_get_status(self, mock_db, client):
        """Test status endpoint return value."""
        from datetime import datetime
        mock_db.get_status.return_value = {
            "status": "RUNNING",
            "last_update": datetime.now().isoformat(),
            "start_time": "2026-08-17T15:00:00",
            "balance": {},
            "positions": []
        }
        res = client.get("/api/status")
        assert res.status_code == 200
        assert res.json()["status"] == "RUNNING"

    @patch('dashboard.dashboard_app.orchestrator')
    @patch('dashboard.dashboard_app.db')
    def test_post_chat(self, mock_db, mock_orchestrator, client):
        """Test sending message to agent orchestrator."""
        # Setup mock return values
        mock_orchestrator.run_analysis = AsyncMock(
            return_value="# BTC Thesis investment report\nSignal is BUY"
        )
        
        # Override the global orchestrator reference
        import dashboard.dashboard_app as da
        da.orchestrator = mock_orchestrator

        payload = {"message": "Generate analysis for BTC", "thread_id": "user123"}
        res = client.post("/api/chat", json=payload)
        
        assert res.status_code == 200
        assert "BTC Thesis" in res.json()["response"]
        mock_db.add_report.assert_called_once_with(
            "BTC", "1h", "Generate analysis for BTC", "# BTC Thesis investment report\nSignal is BUY"
        )

    @patch('dashboard.dashboard_app.db')
    def test_get_reports(self, mock_db, client):
        """Test retrieving historical reports."""
        mock_db.get_reports.return_value = [
            {
                "id": 1,
                "timestamp": "2026-08-17T15:00:00",
                "coin": "BTC",
                "timeframe": "1h",
                "query": "BTC Analysis",
                "report": "Report content"
            }
        ]
        res = client.get("/api/reports")
        assert res.status_code == 200
        assert len(res.json()) == 1
        assert res.json()[0]["coin"] == "BTC"

    @patch('dashboard.dashboard_app.shutil')
    @patch('dashboard.dashboard_app.os')
    def test_upload_rag(self, mock_os, mock_shutil, client):
        """Test uploading document to RAG ingestion folder."""
        mock_os.path.join.return_value = "./data/documents/test.txt"
        
        # Mock RAGService and vector store index
        with patch('app.rag.retriever.RAGService') as mock_rag_cls:
            mock_rag = mock_rag_cls.return_value
            mock_rag.ingest_directory.return_value = 5  # 5 chunks ingested
            
            file_data = {"file": ("test.txt", io.BytesIO(b"Bitcoin is digital gold"), "text/plain")}
            res = client.post("/api/rag/upload", files=file_data)
            
            assert res.status_code == 200
            assert "uploaded and indexed" in res.json()["message"]
            assert res.json()["chunks_ingested"] == 5
