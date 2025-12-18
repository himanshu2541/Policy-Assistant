import logging
from typing import Dict, Type, Any
from langchain_core.retrievers import BaseRetriever
from langchain_classic.retrievers import EnsembleRetriever
from shared.config import Config, config as global_config

from rag_service.interfaces import RetrievalStrategy

logger = logging.getLogger("RAG-Service.Providers.Retrieval")

_RETRIEVAL_REGISTRY: Dict[str, Type[RetrievalStrategy]] = {}

def register_retrieval_strategy(name: str):
    """Decorator to register a retrieval strategy."""
    def decorator(cls):
        _RETRIEVAL_REGISTRY[name] = cls
        return cls
    return decorator


@register_retrieval_strategy("dense")
class DenseRetrievalStrategy(RetrievalStrategy):
    """
    Uses standard semantic similarity search.
    """
    def build_retriever(self, vector_store: Any, settings: Config) -> BaseRetriever:
        logger.info(f"Building Dense Retriever (k={settings.RAG_TOP_K})")
        return vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.RAG_TOP_K}
        )

@register_retrieval_strategy("mmr")
class MMRRetrievalStrategy(RetrievalStrategy):
    """
    Uses Maximal Marginal Relevance to diversify results.
    """
    def build_retriever(self, vector_store: Any, settings: Config) -> BaseRetriever:
        logger.info(f"Building MMR Retriever (k={settings.RAG_TOP_K})")
        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": settings.RAG_TOP_K,
                "fetch_k": settings.RAG_TOP_K * 4,
                "lambda_mult": 0.5
            }
        )

@register_retrieval_strategy("ensemble")
class EnsembleRetrievalStrategy(RetrievalStrategy):
    """
    Combines Dense and MMR results using weighted rank fusion.
    """
    def build_retriever(self, vector_store: Any, settings: Config) -> BaseRetriever:
        weights = settings.RETRIEVAL_WEIGHTS
        logger.info(f"Building Ensemble Retriever. Weights: {weights}")
        
        dense = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.RAG_TOP_K}
        )
        mmr = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": settings.RAG_TOP_K,
                "fetch_k": settings.RAG_TOP_K * 4,
                "lambda_mult": 0.5
            }
        )
        
        return EnsembleRetriever(
            retrievers=[dense, mmr],
            weights=weights
        )

class RetrievalFactory:
    """
    """
    @staticmethod
    def get_retriever(vector_store: Any, settings: Config = global_config) -> BaseRetriever:
        strategy_name = settings.RETRIEVAL_STRATEGY.lower()
        
        strategy_cls = _RETRIEVAL_REGISTRY.get(strategy_name)
        if not strategy_cls:
            valid_options = list(_RETRIEVAL_REGISTRY.keys())
            raise ValueError(f"Unknown Retrieval Strategy: '{strategy_name}'. Valid options: {valid_options}")
            
        strategy = strategy_cls()
        return strategy.build_retriever(vector_store, settings)