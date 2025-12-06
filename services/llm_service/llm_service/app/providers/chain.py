import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from shared.config import config

from shared.providers.llm import LLMProvider

logger = logging.getLogger(__name__)


class ChainProvider:
    """
    Manages the creation of the generation chain (Prompt -> LLM -> Parser).
    Replaces the old 'ChainProvider' but without the retrieval component.
    """

    def __init__(self, config_instance=config):
        self.config = config_instance
        # Initialize the LLM once (OpenAI or Local)
        self.llm = LLMProvider(self.config).get_llm()
        self.output_parser = StrOutputParser()

    def create_chain(self, system_prompt: str = "") -> Runnable:
        """
        Builds the LCEL chain with a dynamic system prompt.
        """
        default_system = """You are a specialized Policy Assistant. 
        You strictly answer questions based ONLY on the provided context below.
        If the answer is not in the context, state "I do not have information on that topic in the policy documents."
        Do not use outside knowledge. (Keep answers elaborative and easy to understand.)
        """

        final_system_prompt = system_prompt if system_prompt else default_system

        # 2. Create Template
        # We expect 'context' and 'input' (user_query) variables
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", final_system_prompt),
                ("system", "Context:\n{context}"),
                ("human", "{input}"),
            ]
        )

        # 3. Build Chain (LCEL)
        # prompt | llm | output_parser
        chain = prompt | self.llm | self.output_parser

        return chain
