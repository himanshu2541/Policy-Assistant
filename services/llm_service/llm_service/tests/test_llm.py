import pytest
from unittest.mock import MagicMock, patch
from llm_service.app.main import LLMService
from llm_service.app.providers.chain import ChainProvider
from shared.protos import service_pb2


@pytest.fixture
def mock_chain_provider():
    """Patches the ChainProvider used by LLMService"""
    with patch("llm_service.app.providers.chain.ChainProvider") as mock:
        yield mock.return_value


@pytest.fixture
def llm_service(mock_chain_provider):
    """Initializes Service with the mock provider"""
    service = LLMService()
    service.chain_provider = mock_chain_provider
    return service


def test_generate_response(llm_service, mock_chain_provider):
    """Test standard unary generation"""
    # 1. Setup Mock Chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = "I am a helpful AI."
    mock_chain_provider.create_chain.return_value = mock_chain

    # 2. Create Request
    request = service_pb2.LLMRequest(
        user_query="Who are you?", context="Some context", system_prompt="Be cool."
    )
    context = MagicMock()

    # 3. Call Service
    response = llm_service.GenerateResponse(request, context)

    # 4. Assertions
    assert response.text == "I am a helpful AI."

    mock_chain_provider.create_chain.assert_called_with("Be cool.")

    mock_chain.invoke.assert_called_once_with(
        {"context": "Some context", "input": "Who are you?"}
    )


def test_stream_response(llm_service, mock_chain_provider):
    """Test streaming generation"""
    # 1. Setup Mock Chain to return an iterator
    mock_chain = MagicMock()
    # Simulate token stream
    mock_chain.stream.return_value = iter(["Hello", " ", "World"])
    mock_chain_provider.create_chain.return_value = mock_chain

    request = service_pb2.LLMRequest(user_query="Hi")
    context = MagicMock()

    # 2. Call Service (Returns generator)
    response_iterator = llm_service.StreamResponse(request, context)

    # 3. Consume Generator
    results = [res.text for res in response_iterator]

    # 4. Assertions
    assert results == ["Hello", " ", "World"]
    mock_chain.stream.assert_called_once()


@patch("llm_service.app.providers.chain.LLMProvider")
def test_chain_provider_logic(mock_provider):
    """Test that ChainProvider constructs a Runnable chain"""
    # Setup Mock LLM
    mock_llm = MagicMock()
    mock_provider.return_value.get_llm.return_value = mock_llm

    provider = ChainProvider()

    # Create a chain
    chain = provider.create_chain(system_prompt="You are a bot")

    # Assertions
    assert provider.llm == mock_llm
    # In LCEL, the resulting object is a RunnableSequence
    # We just verify it's not None and is "runnable-like"
    assert hasattr(chain, "invoke")
    assert hasattr(chain, "stream")
