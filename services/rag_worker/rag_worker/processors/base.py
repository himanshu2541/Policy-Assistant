from abc import ABC, abstractmethod

class BaseFileProcessor(ABC):
    @abstractmethod
    def process(self, file_path: str) -> str | None:
        """Process the file and return extracted text or None if failed."""
        pass