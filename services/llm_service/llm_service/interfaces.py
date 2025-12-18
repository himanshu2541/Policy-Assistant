from abc import ABC, abstractmethod
from langchain_core.runnables import Runnable

class ChainBuilderStrategy(ABC):
    """
    Interface for building LangChain Runnables (Chains).
    """
    @abstractmethod
    def build(self, llm: Runnable, output_parser: Runnable, system_prompt: str = "") -> Runnable:
        """
        Constructs and returns a compiled chain.
        :param llm: The initialized LLM object.
        :param output_parser: The initialized Output Parser.
        :param system_prompt: Optional override for the system prompt.
        """
        pass