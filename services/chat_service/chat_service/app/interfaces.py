from abc import ABC, abstractmethod
from shared.config import Config
from typing import Dict, List, Tuple, Any, Generator, Iterator

from shared.protos import service_pb2

class STTStrategy(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, settings: Config) -> str:
        """
        Transcribes audio bytes and returns the text.
        """
        pass

class ContextRetriever(ABC):
    """Abstracts the logic for retrieving relevant context chunks."""
    @abstractmethod
    def retrieve(self, query: str) -> Tuple[List[Any], str]:
        """
        Returns a tuple: (list_of_chunks, formatted_context_string)
        """
        pass

class AnswerGenerator(ABC):
    """Abstracts the logic for generating answers from an LLM."""
    @abstractmethod
    def generate_response(self, query: str, context: str) -> str:
        """Returns the full response text."""
        pass

    @abstractmethod
    def stream_response(self, query: str, context: str) -> Generator[str, None, None]:
        """Yields text tokens."""
        pass

class PipelineStep(ABC):
    """
    Represents a single step in the RAG processing chain.
    """
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Generator[service_pb2.ChatStreamResponse, None, None]: # type: ignore
        """
        Executes the step logic.
        :param context: A shared dictionary to pass data (like retrieved chunks) between steps.
        :yields: ChatStreamResponse events (thinking, context, answer, etc.)
        """
        pass

class AudioStreamConverter(ABC):
    """
    Interface for converting audio (e.g., WebM -> WAV).
    """
    @abstractmethod
    def convert_bytes(self, data: bytes) -> bytes:
        """
        Converts a full binary buffer (e.g., WebM) into WAV format.
        Useful for batch processing.
        """
        pass