import logging
from pypdf import PdfReader
from .base import BaseFileProcessor

logger = logging.getLogger("RAG-Worker.Processors.PDFProcessor")

class PdfProcessor(BaseFileProcessor):
    def process(self, file_path: str) -> str | None:
        try:
            reader = PdfReader(file_path)
            return "".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            return None