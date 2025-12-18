from langchain_openai import ChatOpenAI
from shared.config import Config, config as global_config
from shared.interfaces import LLMStrategy

class OpenAIStrategy(LLMStrategy):
    def create_llm(self, settings: Config) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=lambda: settings.OPENAI_API_KEY, 
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )

class LocalStrategy(LLMStrategy):
    def create_llm(self, settings: Config) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=lambda: "type-anything", 
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )

class LLMFactory:
    _strategies = {
        "openai": OpenAIStrategy(),
        "local": LocalStrategy()
    }

    @classmethod
    def get_llm(cls, settings: Config = global_config) -> ChatOpenAI:
        provider = settings.LLM_PROVIDER.lower()
        
        strategy = cls._strategies.get(provider)
        if not strategy:
            raise ValueError(f"Unknown LLM Provider: {provider}")
            
        return strategy.create_llm(settings)