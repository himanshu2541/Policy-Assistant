import logging
from langchain_classic.retrievers import EnsembleRetriever

logger = logging.getLogger("RAG-SearchEngine")

class SearchEngine:
    def __init__(self, vector_store):
        """
        :param vector_store: An initialized LangChain VectorStore (Pinecone, Chroma, etc.)
        """
        self.vector_store = vector_store
        self._initialize_retrievers()

    def _initialize_retrievers(self):
        logger.info("Initializing Search Engine Strategy...")

        # RETRIEVER 1: Dense Similarity
        self.dense_retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )

        # RETRIEVER 2: MMR (Maximal Marginal Relevance)
        self.mmr_retriever = self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5}
        )

        # ENSEMBLE RETRIEVER 
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.dense_retriever, self.mmr_retriever],
            weights=[0.6, 0.4]
        )
        logger.info("Ensemble Retriever initialized (Similarity + MMR)")

    def search(self, query: str, top_k: int = 5):
        logger.info(f"Ensemble search for: '{query}'")
        docs = self.ensemble_retriever.invoke(query)
        return docs[:top_k]

    def delete_vector(self, doc_id: str) -> bool:
        if hasattr(self.vector_store, 'delete'):
            # TODO: Verification of delete filter syntax
            self.vector_store.delete(filter={"doc_id": doc_id})
            return True
        return False