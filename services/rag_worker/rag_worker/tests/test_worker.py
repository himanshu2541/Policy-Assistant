import pytest
import json
from unittest.mock import MagicMock, patch
from rag_worker.worker import main as worker_main

# --- Mock Data ---
SAMPLE_JOB = json.dumps({"doc_id": "123", "file_path": "dummy.pdf"})


@patch("rag_worker.worker.Redis")
@patch("rag_worker.worker.PdfReader")
@patch("rag_worker.worker.VectorDatabase")
@patch("rag_worker.worker.EmbeddingsProvider")
def test_worker_processing_flow(mock_emb, mock_vdb, mock_pdf, mock_redis):
    """
    Tests one full cycle: Pop Job -> Read PDF -> Embed -> Upsert
    """
    # 1. Mock Redis
    mock_redis_instance = mock_redis.from_url.return_value

    mock_redis_instance.brpop.side_effect = [
        ("rag_jobs", SAMPLE_JOB),
        KeyboardInterrupt("Stop Loop"),
    ]

    # 2. Mock PDF Reading
    # We mock the pages to return "Page 1 text" when extract_text() is called
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1 text"
    mock_pdf.return_value.pages = [mock_page]

    # 3. Mock Vector Store
    mock_store = mock_vdb.return_value.get_store.return_value

    # 4. Run Worker
    # We expect the KeyboardInterrupt to bubble up and stop the function
    try:
        worker_main()
    except KeyboardInterrupt:
        pass  # Expected behavior to exit the test cleanly

    # 5. Verifications

    # Did it try to read the PDF?
    mock_pdf.assert_called_with("dummy.pdf")

    # Did it add documents to Pinecone/VectorStore?
    mock_store.add_documents.assert_called_once()

    # Verify the document content passed to vector store
    # call_args[0][0] gets the first positional argument (the list of documents)
    added_docs = mock_store.add_documents.call_args[0][0]

    assert len(added_docs) == 1
    assert added_docs[0].page_content == "Page 1 text"
    assert added_docs[0].metadata["doc_id"] == "123"
