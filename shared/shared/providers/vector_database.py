import os
from typing import Any
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores import FAISS
from shared.config import Config, config as global_config
from shared.interfaces import VectorDBStrategy

import logging
logger = logging.getLogger("Shared.Providers.VectorDatabase")
class PineconeStrategy(VectorDBStrategy):
    def create_vector_store(self, embeddings: Any, settings: Config) -> Any:
        # Pinecone requires the index name
        logger.info(f"Creating Pinecone vector store with index: {settings.PINECONE_INDEX_NAME}")
        return PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embeddings,
            pinecone_api_key=settings.PINECONE_API_KEY
        )

class FAISSStrategy(VectorDBStrategy):
    def create_vector_store(self, embeddings: Any, settings: Config) -> Any:
        # Checks if local index exists to load it, otherwise creates new
        logger.info("Creating FAISS vector store")
        index_path = "faiss_index"
        if os.path.exists(index_path):
            return FAISS.load_local(
                index_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
        else:
            # Return an empty store (must be initialized with dummy data or handled by caller)
            # For simplicity, we usually create a new in-memory one or handle initialization elsewhere.
            # Here we return a fresh empty store using a dummy text to init if needed, 
            # or simpler: just the class wrapper if using LangChain's 'from_texts' later.
            # NOTE: FAISS requires data to init. 
            pass 
            # For this example, we assume purely in-memory or handled by IngestionService
            return FAISS.from_texts(["initial_setup"], embeddings)

class VectorDBFactory:
    _strategies = {
        "pinecone": PineconeStrategy(),
        "local": FAISSStrategy() 
    }

    @classmethod
    def get_vector_store(cls, embeddings: Any, settings: Config = global_config) -> Any:
        provider = getattr(settings, "VECTOR_DB_PROVIDER", "pinecone").lower()
        strategy = cls._strategies.get(provider)
        if not strategy:
            raise ValueError(f"Unknown Vector DB Provider: {provider}")
            
        return strategy.create_vector_store(embeddings, settings)