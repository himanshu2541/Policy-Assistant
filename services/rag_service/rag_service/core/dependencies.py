import logging
from functools import lru_cache

from shared.providers.embeddings import EmbeddingFactory
from shared.providers.vector_database import VectorDBFactory
from shared.config import config

logger = logging.getLogger("RAG-Service.Core.Dependencies")

@lru_cache()
def get_embedding_model():
    return EmbeddingFactory.get_embeddings(config)

@lru_cache()
def get_vector_store():
    embeddings = get_embedding_model()
    return VectorDBFactory.get_vector_store(embeddings, config)