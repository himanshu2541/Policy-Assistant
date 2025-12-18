from abc import ABC, abstractmethod
from typing import Any, List
from fastapi import UploadFile
from shared.config import Config
class LLMStrategy(ABC):
    @abstractmethod
    def create_llm(self, settings: Config) -> Any:
        """
        Creates and returns a configured LLM object (e.g., ChatOpenAI).
        """
        pass

class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, file: UploadFile) -> str:
        """
        Saves an uploaded file and returns its accessible path or URI.
        """
        pass
    
class RedisStrategy(ABC):
    @abstractmethod
    def create_client(self, settings: Config, **kwargs) -> Any:
        """
        Creates and returns a Redis client (async).
        Accepts **kwargs for specific connection options (e.g., max_connections).
        """
        pass
    
class EmbeddingStrategy(ABC):
    @abstractmethod
    def create_embedding_model(self, settings: Config) -> Any:
        """
        Returns a LangChain Embeddings model (e.g. OpenAIEmbeddings, HuggingFaceEmbeddings).
        """
        pass
    
class VectorDBStrategy(ABC):
    @abstractmethod
    def create_vector_store(self, embeddings: Any, settings: Config) -> Any:
        """
        Returns a LangChain VectorStore (e.g. Pinecone, FAISS).
        Requires the embedding model to be passed in.
        """
        pass

class VectorStoreManager(ABC):
    """
    Interface for Vector Stores that support CRUD operations.
    Follows ISP by defining the exact contract required by the application,
    avoiding leaky abstractions like 'hasattr' checks.
    """
    @abstractmethod
    def add_documents(self, documents: List[Any]):
        """Adds a list of Document objects to the store."""
        pass

    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """
        Deletes documents matching the specific doc_id.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int) -> List[Any]:
        """Performs a similarity search."""
        pass