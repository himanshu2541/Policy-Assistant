from abc import ABC, abstractmethod
from typing import List

class BaseFileProcessor(ABC):
    @abstractmethod
    def process(self, file_path: str) -> str | None:
        """Process the file and return extracted text or None if failed."""
        pass

class SplitterStrategy(ABC):
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        pass