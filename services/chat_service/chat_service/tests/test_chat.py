import pytest
from unittest.mock import MagicMock, patch, call
from chat_service.app.main import ChatService
from chat_service.app.core.transcriber import TranscriptionService
from chat_service.app.core.pipeline import RAGPipeline
from shared.protos import service_pb2

# ==========================================
# 1. TEST TRANSCRIBER CORE
# ==========================================


@patch("chat_service.app.core.transcriber.STTProvider")
@patch("chat_service.app.core.transcriber.time")
def test_transcriber_process_stream(mock_time, mock_stt_provider):
    """
    Test that the transcriber accumulates buffer and yields events.
    """
    # Setup Mocks
    mock_stt = mock_stt_provider.return_value
    mock_stt.transcribe.side_effect = ["Hello", "Hello World", "Hello World"]  # Simulate growing text

    # Simulate time progressing to trigger intermediate updates
    mock_time.time.side_effect = [
        100.0,
        100.6,
        101.2,
    ]  # 0.6s intervals > 0.5s threshold

    # Setup Input Iterator (2 chunks of audio)
    chunk1 = MagicMock(content=b"audio1")
    chunk2 = MagicMock(content=b"audio2")
    request_iterator = iter([chunk1, chunk2])

    # Initialize Service
    service = TranscriptionService()

    # Run
    responses = list(service.process_stream(request_iterator))

    # Assertions
    # 1. Check if we got "listening" events for each chunk
    listening_events = [r for r in responses if r.event_type == "listening"]
    assert len(listening_events) == 2

    # 2. Check if we got transcription updates
    transcription_events = [r for r in responses if r.event_type == "transcription"]
    assert len(transcription_events) >= 1
    assert transcription_events[-1].text_chunk == "Hello World"

    # 3. Verify STT was called with growing buffer
    # First call: b"audio1", Second call: b"audio1audio2"
    mock_stt.transcribe.assert_has_calls([call(b"audio1"), call(b"audio1audio2")])


# ==========================================
# 2. TEST RAG PIPELINE CORE
# ==========================================


@patch("chat_service.app.core.pipeline.service_pb2_grpc.LLMServiceStub")
@patch("chat_service.app.core.pipeline.service_pb2_grpc.RAGServiceStub")
@patch("chat_service.app.core.pipeline.grpc.insecure_channel")
def test_pipeline_get_answer_unary(mock_channel, mock_rag_stub, mock_llm_stub):
    """
    Test the standard text-in text-out flow.
    """
    # Setup Mocks
    rag_instance = mock_rag_stub.return_value
    llm_instance = mock_llm_stub.return_value

    # Mock RAG Return
    rag_resp = service_pb2.SearchResponse()  # type: ignore
    rag_resp.chunks.add(text="Context 1", doc_id="1")
    rag_instance.RetrieveContext.return_value = rag_resp

    # Mock LLM Return
    llm_instance.GenerateResponse.return_value = service_pb2.LLMResponse(text="Final Answer")  # type: ignore

    # Run
    pipeline = RAGPipeline()
    response = pipeline.get_answer_unary("Question")

    # Assertions
    assert response.text == "Final Answer"
    assert len(response.context_chunks) == 1

    # Verify RAG called with question
    rag_instance.RetrieveContext.assert_called_once()
    assert rag_instance.RetrieveContext.call_args[0][0].query_text == "Question"

    # Verify LLM called with Context + Question
    llm_instance.GenerateResponse.assert_called_once()
    llm_arg = llm_instance.GenerateResponse.call_args[0][0]
    assert "Context 1" in llm_arg.context
    assert llm_arg.user_query == "Question"


# ==========================================
# 3. TEST SERVICE ORCHESTRATOR (MAIN)
# ==========================================


@pytest.fixture
def mock_cores():
    """Patches both the Transcriber and Pipeline used by main.py"""
    with patch("chat_service.app.main.TranscriptionService") as mock_trans, patch(
        "chat_service.app.main.RAGPipeline"
    ) as mock_pipe:
        yield (mock_trans.return_value, mock_pipe.return_value)


def test_interact_endpoint(mock_cores):
    """Test /interact just delegates to pipeline"""
    _, mock_pipeline = mock_cores
    mock_pipeline.get_answer_unary.return_value = "Success"

    service = ChatService()
    request = MagicMock(user_query="Hi")

    result = service.Interact(request, MagicMock())

    assert result == "Success"
    mock_pipeline.get_answer_unary.assert_called_with("Hi")


def test_stream_audio_chat(mock_cores):
    """Test the full audio flow: Transcribe -> Pipeline"""
    mock_transcriber, mock_pipeline = mock_cores

    # 1. Mock Transcriber Generator
    # It yields a transcription event, then finishes
    mock_transcriber.process_stream.return_value = iter(
        [
            service_pb2.ChatStreamResponse(  # type: ignore
                event_type="transcription", text_chunk="Hello AI"
            )
        ]
    )

    # 2. Mock Pipeline Generator
    # It yields an answer event
    mock_pipeline.get_answer_stream.return_value = iter(
        [service_pb2.ChatStreamResponse(event_type="answer", text_chunk="Hello Human")]  # type: ignore
    )

    service = ChatService()
    request_iterator = MagicMock()  # Dummy iterator

    # Run
    responses = list(service.StreamAudioChat(request_iterator, MagicMock()))

    # Assertions

    # Did we get the transcription?
    assert responses[0].text_chunk == "Hello AI"
    assert responses[0].event_type == "transcription"

    # Did we get the answer from the pipeline?
    assert responses[1].text_chunk == "Hello Human"
    assert responses[1].event_type == "answer"

    # Did we get the 'done' signal?
    assert responses[-1].event_type == "done"

    # Verify Data Handoff: Did the pipeline receive the text from the transcriber?
    mock_pipeline.get_answer_stream.assert_called_with("Hello AI")
