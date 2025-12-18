import os
import logging
from typing import Any, Dict, Type
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores import FAISS
from shared.config import Config, config as global_config
from shared.interfaces import VectorDBStrategy, VectorStoreManager
from typing import List

logger = logging.getLogger("Shared.Providers.VectorDatabase")

# Registry
_VECTOR_DB_REGISTRY: Dict[str, Type[VectorDBStrategy]] = {}

def register_vector_db_strategy(name: str):
    def decorator(cls):
        _VECTOR_DB_REGISTRY[name] = cls
        return cls
    return decorator

class PineconeAdapter(VectorStoreManager):
    def __init__(self, store: PineconeVectorStore):
        self.store = store

    def add_documents(self, documents: List[Any]):
        self.store.add_documents(documents)

    def similarity_search(self, query: str, k: int) -> List[Any]:
        return self.store.similarity_search(query, k=k)

    def delete_document(self, doc_id: str) -> bool:
        try:
            self.store.delete(filter={"doc_id": doc_id})
            return True
        except Exception as e:
            logger.error(f"Pinecone delete failed for {doc_id}: {e}")
            return False
    
    def as_langchain_retriever(self, search_type: str, search_kwargs: dict):
        return self.store.as_retriever(search_type=search_type, search_kwargs=search_kwargs)

class FAISSAdapter(VectorStoreManager):
    def __init__(self, store: FAISS):
        self.store = store

    def add_documents(self, documents: List[Any]):
        self.store.add_documents(documents)

    def similarity_search(self, query: str, k: int) -> List[Any]:
        return self.store.similarity_search(query, k=k)

    def delete_document(self, doc_id: str) -> bool:
        # FAISS Local often relies on internal IDs, not metadata.
        # We normalize the behavior: instead of crashing or needing hasattr,
        # we strictly return False to indicate "Not Supported/Failed" cleanly.
        logger.warning(f"Delete operation not supported/implemented for FAISS Local adapter (doc_id: {doc_id})")
        return False
    
    def as_langchain_retriever(self, search_type: str, search_kwargs: dict):
        return self.store.as_retriever(search_type=search_type, search_kwargs=search_kwargs)
    
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