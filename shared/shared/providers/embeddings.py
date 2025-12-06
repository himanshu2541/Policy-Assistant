import logging
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from shared.config import config

logger = logging.getLogger("shared.providers.embeddings")


class EmbeddingsProvider:
    """
    Provides methods to initialize and retrieve embedding models.
    """

    def __init__(self, config_instance=config):
        self.config = config_instance
        self.embeddings = self._get_embeddings()

    def _get_embeddings(self) -> Embeddings:
        provider = self.config.EMBEDDING_PROVIDER.lower()

        try:
            if provider == "openai":
                return OpenAIEmbeddings(
                    model=self.config.EMBEDDING_MODEL_NAME,
                    api_key=lambda: self.config.OPENAI_API_KEY,  # Pass value directly if not using callable
                )
            elif provider == "local":
                return HuggingFaceEmbeddings(
                    model_name=self.config.EMBEDDING_MODEL_NAME,
                    model_kwargs={"device": "cpu"},
                )
            else:
                raise ValueError(f"Unknown embedding provider: {provider}")

        except Exception as e:
            logger.error(
                f"Failed to initialize embedding model (provider: {provider}): {e}"
            )
            raise

    def get_embeddings(self) -> Embeddings:
        return self.embeddings