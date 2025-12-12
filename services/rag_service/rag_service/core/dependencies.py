import logging
from functools import lru_cache

from shared.config import config
from shared.providers.embeddings import EmbeddingsProvider
from shared.providers.vector_database import VectorDatabase

logger = logging.getLogger("RAG-Core")

@lru_cache()
def get_embedding_model():
    """Singleton Embedding Model"""
    logger.info("Loading Embedding Model...")
    return EmbeddingsProvider(config).get_embeddings()

@lru_cache()
def get_vector_store():
    """
    Singleton connection to the Vector Database.
    This handles the actual connection logic.
    """
    logger.info("Connecting to Vector Database...")
    embeddings = get_embedding_model()
    return VectorDatabase(embeddings, config).get_store()