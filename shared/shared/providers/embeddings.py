from typing import Any, Dict, Type
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from shared.config import Config, config as global_config
from shared.interfaces import EmbeddingStrategy

_EMBEDDING_REGISTRY: Dict[str, Type[EmbeddingStrategy]] = {}

def register_embedding_strategy(name: str):
    """Decorator to register an Embedding strategy."""
    def decorator(cls):
        _EMBEDDING_REGISTRY[name] = cls
        return cls
    return decorator

@register_embedding_strategy("openai")
class OpenAIEmbeddingStrategy(EmbeddingStrategy):
    def create_embedding_model(self, settings: Config) -> Any:
        return OpenAIEmbeddings(
            api_key=lambda: settings.OPENAI_API_KEY
        )

@register_embedding_strategy("local")
class LocalEmbeddingStrategy(EmbeddingStrategy):
    def create_embedding_model(self, settings: Config) -> Any:
        return HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME
        )

class EmbeddingFactory:
    """
    Factory to retrieve Embedding strategies.
    Decoupled from concrete implementations via the _EMBEDDING_REGISTRY.
    """
    @staticmethod
    def get_embeddings(settings: Config = global_config) -> Any:
        provider = settings.EMBEDDING_PROVIDER.lower()
        
        strategy_cls = _EMBEDDING_REGISTRY.get(provider)
        if not strategy_cls:
            raise ValueError(f"Unknown Embedding Provider: {provider}. Available: {list(_EMBEDDING_REGISTRY.keys())}")
        
        strategy = strategy_cls()
        return strategy.create_embedding_model(settings)