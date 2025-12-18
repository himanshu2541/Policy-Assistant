from abc import ABC, abstractmethod
from langchain_core.retrievers import BaseRetriever
from shared.config import Config
from typing import Any

class RetrievalStrategy(ABC):
    """
    Abstract Base Class for Retrieval Strategies.
    """
    @abstractmethod
    def build_retriever(self, vector_store: Any, settings: Config) -> BaseRetriever:
        """
        Constructs and returns a LangChain Retriever.
        """
        pass