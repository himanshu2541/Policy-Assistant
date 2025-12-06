import pytest
from unittest.mock import MagicMock, patch
from rag_service.app.main import RAGService
from shared.protos import service_pb2


@pytest.fixture
def rag_service():
    """Initializes RAGService with mocked dependencies"""
    with patch("rag_service.app.main.Redis") as mock_redis, patch(
        "rag_service.app.main.VectorDatabase"
    ) as mock_vdb, patch("rag_service.app.main.EmbeddingsProvider") as mock_emb:

        service = RAGService()
        service.redis = mock_redis.return_value
        service.vector_db = mock_vdb.return_value.get_store.return_value
        return service


def test_trigger_sync(rag_service):
    """Test that TriggerSync pushes to Redis"""
    request = MagicMock(doc_id="doc_1", file_path="/data/doc.pdf")
    context = MagicMock()

    response = rag_service.TriggerSync(request, context)

    assert response.status == "Queued"
    rag_service.redis.lpush.assert_called_once()
    args, _ = rag_service.redis.lpush.call_args

    # FIX: assert actual payload content
    assert "rag_jobs" in args
    assert "doc_1" in args[1]
    assert "/data/doc.pdf" in args[1]


def test_retrieve_context(rag_service):
    """Test that RetrieveContext queries Vector DB"""
    mock_doc = MagicMock()
    mock_doc.page_content = "Policy Content"
    mock_doc.metadata = {"doc_id": "doc_1"}

    rag_service.vector_db.similarity_search_with_score.return_value = [(mock_doc, 0.95)]

    request = service_pb2.SearchRequest(query_text="policy", top_k=2)  # type: ignore
    context = MagicMock()

    response = rag_service.RetrieveContext(request, context)

    assert len(response.chunks) == 1
    assert response.chunks[0].text == "Policy Content"
    # FIX: Approximate comparison
    assert response.chunks[0].score == pytest.approx(0.95, rel=1e-4)
