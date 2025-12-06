import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock # <--- Import AsyncMock

from api_gateway.app.main import app
from shared.protos import service_pb2

client = TestClient(app)

@pytest.fixture
def mock_rag_stub():
    with patch("api_gateway.app.routes.vectors.service_pb2_grpc.RAGServiceStub") as mock:
        yield mock.return_value

@pytest.fixture
def mock_chat_stub():
    with patch("api_gateway.app.routes.chat.service_pb2_grpc.ChatServiceStub") as mock:
        yield mock.return_value

# ... (Root and Health tests remain the same) ...

def test_upload_endpoint():
    """Test standard file upload (HTTP)"""
    files = {"file": ("test_policy.pdf", b"%PDF-1.4 content...", "application/pdf")}
    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 200
    assert response.json()["doc_id"] == "test_policy.pdf"

def test_sync_endpoint(mock_rag_stub):
    """Test /sync calls RAG Service gRPC"""
    # Setup Mock Response
    mock_response = service_pb2.SyncResponse(status="Queued", job_id="12345") # type: ignore
    
    # FIX: Use AsyncMock so 'await stub.TriggerSync()' works
    mock_rag_stub.TriggerSync = AsyncMock(return_value=mock_response)

    payload = {"doc_id": "doc_1", "filename": "test.pdf"}
    response = client.post("/api/v1/vectors/sync", json=payload)

    assert response.status_code == 200
    assert response.json()["job_id"] == "12345"
    mock_rag_stub.TriggerSync.assert_called_once()

def test_chat_endpoint(mock_chat_stub):
    """Test /chat calls Chat Service gRPC"""
    # Setup Mock Response
    mock_response = service_pb2.ChatResponse(text="Hello human") # type: ignore
    mock_response.context_chunks.add(text="Policy info...", doc_id="doc_1", score=0.9)
    
    # FIX: Use AsyncMock so 'await stub.Interact()' works
    # This creates a coroutine that returns mock_response when awaited
    mock_chat_stub.Interact = AsyncMock(return_value=mock_response)

    payload = {"query": "What is the policy?", "session_id": "abc"}
    response = client.post("/api/v1/chat", json=payload)

    assert response.status_code == 200
    assert response.json()["answer"] == "Hello human"
    assert len(response.json()["contexts"]) == 1