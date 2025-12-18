import os
import logging
from typing import Dict, Type, List
from rag_worker.interfaces import BaseFileProcessor

logger = logging.getLogger("RAG-Worker.Processors.Factory")

_PROCESSOR_REGISTRY: Dict[str, Type[BaseFileProcessor]] = {}

def register_processor(extensions: List[str]):
    """
    Decorator to register a processor for specific file extensions.
    Example: @register_processor([".pdf"])
    """
    def decorator(cls):
        for ext in extensions:
            _PROCESSOR_REGISTRY[ext.lower()] = cls
        return cls
    return decorator

class ProcessorFactory:
    @staticmethod
    def get_processor(file_path: str) -> BaseFileProcessor | None:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        processor_cls = _PROCESSOR_REGISTRY.get(ext)
        if not processor_cls:
            logger.warning(f"No processor registered for extension: {ext}")
            return None
            
        return processor_cls()
    
@register_processor([".pdf"])
class PdfProcessor(BaseFileProcessor):
    def process(self, file_path: str) -> str | None:
        from pypdf import PdfReader
        try:
            reader = PdfReader(file_path)
            return "".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            return None

@register_processor([".txt", ".md", ".json", ".csv"])
class TextProcessor(BaseFileProcessor):
    def process(self, file_path: str) -> str | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            return None