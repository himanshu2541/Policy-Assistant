import logging
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from shared.config import Config
from shared.providers.llm import LLMFactory
from llm_service.app.providers.chain_strategies import ChainBuilderFactory

logger = logging.getLogger("LLM-Service.Providers.Chain")


class ChainProvider:
    """
    Manages the creation of generation chains using the Strategy Pattern.
    """

    def __init__(self, settings: Config):
        self.config = settings
        # Initialize Infrastructure (LLM & Parser)
        self.llm = LLMFactory.get_llm(self.config)
        self.output_parser = StrOutputParser()

    def create_chain(
        self, system_prompt: str = "", strategy_type: str = "policy_chat"
    ) -> Runnable:
        """
        Builds the LCEL chain using a selected strategy.

        :param system_prompt: Optional override for system prompt.
        :param strategy_type: The key for the strategy (e.g., 'policy_chat', 'summarization').
        Defaults to 'policy_chat'.
        """
        builder = ChainBuilderFactory.get_builder(strategy_type)

        chain = builder.build(
            llm=self.llm, output_parser=self.output_parser, system_prompt=system_prompt
        )

        logger.info(f"Created chain using strategy: {strategy_type}")
        return chain
