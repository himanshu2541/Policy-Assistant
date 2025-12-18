from abc import ABC, abstractmethod
from shared.config import Config

class STTStrategy(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, settings: Config) -> str:
        """
        Transcribes audio bytes and returns the text.
        """
        pass