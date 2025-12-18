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

class JobStatusReporter(ABC):
    @abstractmethod
    async def report_success(self, doc_id: str, filename: str, chunk_count: int):
        pass

    @abstractmethod
    async def report_failure(self, doc_id: str, filename: str, error_message: str):
        pass