import logging
from rag_service.providers.retrieval import RetrievalFactory
from shared.config import config

logger = logging.getLogger("RAG-SearchEngine")


class SearchEngine:
    def __init__(self, vector_store, config_instance=config):
        """
        :param vector_store: An initialized LangChain VectorStore (Pinecone, Chroma, etc.)
        :param config_instance: Configuration settings
        """
        self.vector_store = vector_store
        self.config = config_instance

        self.retriever = RetrievalFactory.get_retriever(self.vector_store, self.config)
        logger.info("Search Engine initialized successfully.")

    def search(self, query: str, top_k: int = None): # type: ignore
        """
        Executes the search using the configured strategy.
        :param top_k: Optional override for number of results to return.
        """
        logger.info(
            f"Searching for: '{query}' using strategy: {self.config.RETRIEVAL_STRATEGY}"
        )

        docs = self.retriever.invoke(query)

        if top_k:
            return docs[:top_k]
        return docs

    def delete_vector(self, doc_id: str) -> bool:
        """
        Deletes a vector from the store by doc_id.
        """
        if hasattr(self.vector_store, "delete"):
            try:
                # Depending on the VectorStore implementation (Pinecone, Chroma, FAISS),
                # the delete signature might vary.
                self.vector_store.delete(filter={"doc_id": doc_id})
                logger.info(f"Deleted vector: {doc_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting vector {doc_id}: {e}")
                return False

        logger.warning("Vector store does not support deletion.")
        return False
