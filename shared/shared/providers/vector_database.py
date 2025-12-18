import os
import logging
from typing import Any, Dict, Type
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores import FAISS
from shared.config import Config, config as global_config
from shared.interfaces import VectorDBStrategy

logger = logging.getLogger("Shared.Providers.VectorDatabase")

# Registry
_VECTOR_DB_REGISTRY: Dict[str, Type[VectorDBStrategy]] = {}

def register_vector_db_strategy(name: str):
    def decorator(cls):
        _VECTOR_DB_REGISTRY[name] = cls
        return cls
    return decorator

@register_vector_db_strategy("pinecone")
class PineconeStrategy(VectorDBStrategy):
    def create_vector_store(self, embeddings: Any, settings: Config) -> Any:
        logger.info(f"Creating Pinecone vector store with index: {settings.PINECONE_INDEX_NAME}") #
        return PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embeddings,
            pinecone_api_key=settings.PINECONE_API_KEY
        )

@register_vector_db_strategy("local")
class FAISSStrategy(VectorDBStrategy):
    def create_vector_store(self, embeddings: Any, settings: Config) -> Any:
        logger.info("Creating FAISS vector store")
        index_path = "faiss_index"
        
        if os.path.exists(index_path):
            return FAISS.load_local(
                index_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
        
        # Fallback/Init logic
        return FAISS.from_texts(["initial_setup"], embeddings)

class VectorDBFactory:
    @staticmethod
    def get_vector_store(embeddings: Any, settings: Config = global_config) -> Any:
        # Default to pinecone if not specified, matching original logic behavior
        provider = getattr(settings, "VECTOR_DB_PROVIDER", "pinecone").lower() 
        
        strategy_cls = _VECTOR_DB_REGISTRY.get(provider)
        if not strategy_cls:
            raise ValueError(f"Unknown Vector DB Provider: {provider}")
            
        strategy = strategy_cls()
        return strategy.create_vector_store(embeddings, settings)