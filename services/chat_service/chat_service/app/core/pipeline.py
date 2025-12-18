import logging
from shared.protos import service_pb2
from shared.config import Config
from chat_service.app.interfaces import ContextRetriever, AnswerGenerator

logger = logging.getLogger("Chat-Service.Core.Pipeline")

import logging
from typing import List
from shared.protos import service_pb2
from chat_service.app.interfaces import PipelineStep

logger = logging.getLogger("Chat-Service.Core.Pipeline")

class FlexiblePipeline:
    def __init__(self, steps: List[PipelineStep]):
        """
        :param steps: An ordered list of steps to execute.
        """
        self.steps = steps

    def run_stream(self, query_text: str):
        """
        Executes the pipeline steps sequentially.
        """
        if not query_text:
            return

        # Shared context dictionary initialized with the input
        context = {"query": query_text}

        try:
            for step in self.steps:
                # Delegate execution to the step
                yield from step.execute(context)
                
        except Exception as e:
            logger.error(f"Pipeline Stream Error: {e}")
            yield service_pb2.ChatStreamResponse( # type: ignore
                text_chunk="I encountered an error processing your request.",
                event_type="error",
            )

    def run_unary(self, query_text: str) -> service_pb2.ChatResponse: # type: ignore
        """
        Non-streaming wrapper (consumes the stream to build a single response).
        Useful for endpoints that don't support streaming.
        """
        full_text = []
        chunks = []
        
        for event in self.run_stream(query_text):
            if event.event_type == "answer" and event.text_chunk:
                full_text.append(event.text_chunk)
            elif event.event_type == "context" and event.context_chunks:
                chunks.extend(event.context_chunks)
        
        return service_pb2.ChatResponse( # type: ignore
            text="".join(full_text), 
            context_chunks=chunks
        )

# class RAGPipeline:
#     def __init__(
#         self,
#         retriever: ContextRetriever,
#         generator: AnswerGenerator,
#         settings: Config,
#     ):
#         self.config = settings
#         self.retriever = retriever
#         self.generator = generator

#     def get_answer_stream(self, query_text: str):
#         if not query_text:
#             return

#         try:
#             # 1. Retrieve Context
#             yield service_pb2.ChatStreamResponse(event_type="thinking")  # type: ignore

#             chunks, context_str = self.retriever.retrieve(query_text)

#             yield service_pb2.ChatStreamResponse(  # type: ignore
#                 context_chunks=chunks, event_type="context"
#             )

#             # 2. Stream LLM Answer
#             logger.info("Starting LLM streaming response")
#             for token in self.generator.stream_response(query_text, context_str):
#                 yield service_pb2.ChatStreamResponse(  # type: ignore
#                     text_chunk=token, event_type="answer"
#                 )

#         except Exception as e:
#             logger.error(f"Pipeline Stream Error: {e}")
#             yield service_pb2.ChatStreamResponse(  # type: ignore
#                 text_chunk="I encountered an error processing your request.",
#                 event_type="error",
#             )

#     def get_answer_unary(self, query_text: str) -> service_pb2.ChatResponse:  # type: ignore
#         """
#         Non-streaming version for the /chat endpoint.
#         """
#         try:
#             chunks, context_str = self._get_context(query_text)  # type: ignore

#             logger.info("Generating LLM response (Unary)")
#             text = self.generator.generate_response(
#                 query_text,
#                 context_str,
#             )

#             return service_pb2.ChatResponse(text=text, context_chunks=chunks)  # type: ignore
#         except Exception as e:
#             logger.error(f"Pipeline Unary Error: {e}")
#             # Return empty or error response depending on proto definition
#             return service_pb2.ChatResponse(text="Internal Error")  # type: ignore
