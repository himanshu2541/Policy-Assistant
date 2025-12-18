from abc import ABC, abstractmethod
from shared.config import Config
from typing import List, Tuple, Any, Generator

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