import logging
from typing import List, Dict, Type
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
from shared.config import Config, config as global_config
from rag_worker.interfaces import SplitterStrategy

logger = logging.getLogger("RAG-Worker.Providers.Splitter")

_SPLITTER_REGISTRY: Dict[str, Type[SplitterStrategy]] = {}


def register_splitter_strategy(name: str):
    """Decorator to register a Splitting strategy."""

    def decorator(cls):
        _SPLITTER_REGISTRY[name] = cls
        return cls

    return decorator


@register_splitter_strategy("recursive")
class RecursiveSplitterStrategy(SplitterStrategy):
    def __init__(self, settings: Config):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
        )

    def split_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)


@register_splitter_strategy("token")
class TokenSplitterStrategy(SplitterStrategy):
    def __init__(self, settings: Config):
        # Example: Token-based splitting (useful for strict context windows)
        self.splitter = TokenTextSplitter(
            chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
        )

    def split_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)


class TextSplitterFactory:
    """
    Factory to retrieve Text Splitter strategies.
    """

    @staticmethod
    def get_splitter(settings: Config = global_config) -> SplitterStrategy:
        provider = getattr(settings, "SPLITTER_PROVIDER", "recursive").lower()

        strategy_cls = _SPLITTER_REGISTRY.get(provider)
        if not strategy_cls:
            valid_keys = list(_SPLITTER_REGISTRY.keys())
            raise ValueError(
                f"Unknown Splitter Provider: {provider}. Available: {valid_keys}"
            )

        logger.info(f"Initializing Text Splitter Strategy: {provider}")
        return strategy_cls()
