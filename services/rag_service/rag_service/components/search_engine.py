import logging
from shared.config import Config
from shared.interfaces import VectorStoreManager

logger = logging.getLogger("RAG-Service.Components.SearchEngine")


class SearchEngine:
    def __init__(self, vector_store: VectorStoreManager, settings: Config):
        """
        :param vector_store: An initialized LangChain VectorStore (Pinecone, Chroma, etc.)
        :param settings: Configuration settings
        """
        self.vector_store = vector_store
        self.config = settings

        logger.info("Search Engine initialized successfully.")

    def search(self, query: str, top_k: int = None):  # type: ignore
        """
        Executes the search using the configured strategy.
        :param top_k: Optional override for number of results to return.
        """

        k = top_k if top_k else 4
        logger.info(f"Executing search for query: '{query}' with top_k={k}")

        docs = self.vector_store.similarity_search(query, k=k)
        if top_k:
            return docs[:top_k]
        return docs

    def delete_vector(self, doc_id: str) -> bool:
        """
        Deletes a vector from the store by doc_id.
        """
        success = self.vector_store.delete_document(doc_id)

        if success:
            logger.info(f"Deleted vector: {doc_id}")
        else:
            logger.warning(f"Failed to delete vector (or not supported): {doc_id}")

        return success
