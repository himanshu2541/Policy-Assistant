import logging
from .base import BaseFileProcessor

logger = logging.getLogger("RAG-Worker.Processors.TextProcessor")

class TextProcessor(BaseFileProcessor):
    def process(self, file_path: str) -> str | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            return None