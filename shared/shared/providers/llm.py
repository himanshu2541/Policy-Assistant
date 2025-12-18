from typing import Dict, Type
from langchain_openai import ChatOpenAI
from shared.config import Config, config as global_config
from shared.interfaces import LLMStrategy

_LLM_REGISTRY: Dict[str, Type[LLMStrategy]] = {}

def register_llm_strategy(name: str):
    """Decorator to register an LLM strategy."""
    def decorator(cls):
        _LLM_REGISTRY[name] = cls
        return cls
    return decorator

@register_llm_strategy("openai")
class OpenAIStrategy(LLMStrategy):
    def create_llm(self, settings: Config) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=lambda: settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )

@register_llm_strategy("local")
class LocalStrategy(LLMStrategy):
    def create_llm(self, settings: Config) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=lambda: "type-anything",  #
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )

class LLMFactory:
    """
    Factory to retrieve LLM strategies.
    Decoupled from concrete implementations via the _LLM_REGISTRY.
    """
    @staticmethod
    def get_llm(settings: Config = global_config) -> ChatOpenAI:
        provider = settings.LLM_PROVIDER.lower()
        
        strategy_cls = _LLM_REGISTRY.get(provider)
        if not strategy_cls:
            raise ValueError(f"Unknown LLM Provider: {provider}. Available: {list(_LLM_REGISTRY.keys())}")
            
        # Instantiate and use the strategy
        strategy = strategy_cls()
        return strategy.create_llm(settings)