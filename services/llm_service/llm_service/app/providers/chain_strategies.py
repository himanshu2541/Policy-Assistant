import logging
from typing import Dict, Type, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from llm_service.interfaces import ChainBuilderStrategy

logger = logging.getLogger("LLM-Service.Providers.ChainStrategies")

_CHAIN_REGISTRY: Dict[str, Type[ChainBuilderStrategy]] = {}

def register_chain_strategy(name: str):
    """Decorator to register a Chain Builder strategy."""
    def decorator(cls):
        _CHAIN_REGISTRY[name] = cls
        return cls
    return decorator

@register_chain_strategy("policy_chat")
class PolicyChatStrategy(ChainBuilderStrategy):
    """
    Standard RAG-based Policy Assistant Chat.
    """
    def build(self, llm: Runnable, output_parser: Runnable, system_prompt: str = "") -> Runnable:
        default_system = """You are a specialized Policy Assistant. 
        You strictly answer questions based ONLY on the provided context below.
        If the answer is not in the context, state "I do not have information on that topic in the policy documents."
        Do not use outside knowledge. (Keep answers concise and easy to understand.)
        """
        final_prompt = system_prompt if system_prompt else default_system

        # Context + Input
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", final_prompt),
                ("system", "Context:\n{context}"),
                ("human", "{input}"),
            ]
        )
        return prompt_template | llm | output_parser

@register_chain_strategy("summarization")
class SummarizationStrategy(ChainBuilderStrategy):
    """
    Strategy specifically for summarizing documents.
    """
    def build(self, llm: Runnable, output_parser: Runnable, system_prompt: str = "") -> Runnable:
        default_system = "You are an expert summarizer. Summarize the following text concisely."
        final_prompt = system_prompt if system_prompt else default_system
        
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", final_prompt),
                ("human", "{input}"),
            ]
        )
        return prompt_template | llm | output_parser

@register_chain_strategy("general")
class GeneralChatStrategy(ChainBuilderStrategy):
    """
    General purpose chat without strict RAG constraints.
    """
    def build(self, llm: Runnable, output_parser: Runnable, system_prompt: str = "") -> Runnable:
        default_system = "You are a helpful AI assistant."
        final_prompt = system_prompt if system_prompt else default_system

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", final_prompt),
                ("human", "{input}"),
            ]
        )
        return prompt_template | llm | output_parser

class ChainBuilderFactory:
    """
    Factory to retrieve Chain Builder strategies.
    """
    @staticmethod
    def get_builder(strategy_name: str) -> ChainBuilderStrategy:
        strategy_cls = _CHAIN_REGISTRY.get(strategy_name.lower())
        if not strategy_cls:
            logger.warning(f"Unknown Chain Strategy '{strategy_name}', defaulting to 'policy_chat'")
            strategy_cls = _CHAIN_REGISTRY["policy_chat"]
            
        return strategy_cls()