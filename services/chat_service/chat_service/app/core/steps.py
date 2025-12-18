import logging
from typing import Dict, Any, Generator
from shared.protos import service_pb2
from chat_service.app.interfaces import PipelineStep, ContextRetriever, AnswerGenerator

logger = logging.getLogger("Chat-Service.Core.Steps")

class ThinkingStep(PipelineStep):
    """Emits the initial 'thinking' event."""
    def execute(self, context: Dict[str, Any]) -> Generator[service_pb2.ChatStreamResponse, None, None]: # type: ignore
        yield service_pb2.ChatStreamResponse(event_type="thinking") # type: ignore

class RetrievalStep(PipelineStep):
    """Handles vector search and context retrieval."""
    def __init__(self, retriever: ContextRetriever):
        self.retriever = retriever

    def execute(self, context: Dict[str, Any]) -> Generator[service_pb2.ChatStreamResponse, None, None]: # type: ignore
        query = context.get("query")
        if not query:
            logger.warning("RetrievalStep: No query found in context.")
            return

        # Perform Retrieval
        chunks, context_str = self.retriever.retrieve(query)
        
        # Store results in shared context for future steps (e.g., Generation)
        context["chunks"] = chunks
        context["context_str"] = context_str
        
        # Emit Context Event
        yield service_pb2.ChatStreamResponse( # type: ignore
            context_chunks=chunks, event_type="context"
        )

class GenerationStep(PipelineStep):
    """Handles LLM generation based on query and context."""
    def __init__(self, generator: AnswerGenerator):
        self.generator = generator

    def execute(self, context: Dict[str, Any]) -> Generator[service_pb2.ChatStreamResponse, None, None]: # type: ignore
        query = context.get("query")
        context_str = context.get("context_str", "")
        
        if not query:
            return

        logger.info("Starting LLM streaming response")
        
        # Stream from LLM
        for token in self.generator.stream_response(query, context_str):
            yield service_pb2.ChatStreamResponse( # type: ignore
                text_chunk=token, event_type="answer"
            )