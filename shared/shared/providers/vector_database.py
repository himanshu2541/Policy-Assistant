import logging
from langchain_pinecone import PineconeVectorStore

from shared.config import config

logger = logging.getLogger("shared.providers.vector_database")


class VectorDatabase:
    """
    Manages the initialization and connection to the vector store.
    """

    def __init__(self, embeddings, config_instance=config):
        self.config = config_instance
        self.embeddings = embeddings
        self.pinecone_store = self._get_pinecone_store()

    def _get_pinecone_store(self) -> PineconeVectorStore:
        try:
            if not self.config.PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY is required.")

            store = PineconeVectorStore(
                index_name=self.config.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                pinecone_api_key=self.config.PINECONE_API_KEY,
            )
            logger.info(
                f"Connected to Pinecone index: {self.config.PINECONE_INDEX_NAME}"
            )
            return store

        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            raise

    def get_store(self):
        return self.pinecone_store
