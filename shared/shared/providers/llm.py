import logging
from langchain_openai import ChatOpenAI
from shared.config import config

logger = logging.getLogger("shared.providers.llm")


class LLMProvider:
    """
    Provides a unified interface for LLMs (Cloud or Local).
    """

    def __init__(self, config_instance=config):
        self.config = config_instance
        self.llm = self._get_llm()

    def _get_llm(self) -> ChatOpenAI:
        provider = self.config.LLM_PROVIDER.lower()

        try:
            if provider == "openai":
                logger.info(f"Initializing OpenAI Model: {self.config.LLM_MODEL}")
                return ChatOpenAI(
                    model=self.config.LLM_MODEL,
                    api_key=lambda: self.config.OPENAI_API_KEY,
                    temperature=self.config.LLM_TEMPERATURE,
                )

            elif provider == "local":
                # Connects to LM Studio, Ollama, or vLLM
                logger.info(f"Connecting to Local LLM at: {self.config.LLM_BASE_URL}")
                return ChatOpenAI(
                    base_url=self.config.LLM_BASE_URL,
                    api_key=lambda: "type-anything",
                    model=self.config.LLM_MODEL,
                    temperature=self.config.LLM_TEMPERATURE,
                )

            else:
                raise ValueError(f"Unknown LLM Provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def get_llm(self):
        return self.llm
