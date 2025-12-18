from typing import Any
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from shared.config import Config, config as global_config
from shared.interfaces import EmbeddingStrategy

class OpenAIEmbeddingStrategy(EmbeddingStrategy):
    def create_embedding_model(self, settings: Config) -> Any:
        return OpenAIEmbeddings(
            api_key=lambda: settings.OPENAI_API_KEY
        )

class LocalEmbeddingStrategy(EmbeddingStrategy):
    def create_embedding_model(self, settings: Config) -> Any:
        # Uses standard HuggingFace SentenceTransformers
        return HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME
        )

class EmbeddingFactory:
    _strategies = {
        "openai": OpenAIEmbeddingStrategy(),
        "local": LocalEmbeddingStrategy()
    }

    @classmethod
    def get_embeddings(cls, settings: Config = global_config) -> Any:
        provider = settings.EMBEDDING_PROVIDER.lower()
        strategy = cls._strategies.get(provider)
        if not strategy:
            raise ValueError(f"Unknown Embedding Provider: {provider}")
        
        return strategy.create_embedding_model(settings)