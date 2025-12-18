import logging
from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config

logger = logging.getLogger("Chat-Service.Core.Pipeline")


class RAGPipeline:
    def __init__(self, rag_stub, llm_stub, config_instance=config):
        self.config = config_instance
        self.rag_stub = rag_stub
        self.llm_stub = llm_stub

    def _get_context(self, query_text: str):
        """
        Helper method to retrieve and format context (DRY Principle).
        """
        logger.info(f"Retrieving context for: '{query_text[:50]}...'")

        # Use config for top_k instead of hardcoding
        k = getattr(self.config, "RAG_TOP_K", 3)

        rag_resp = self.rag_stub.RetrieveContext(
            service_pb2.SearchRequest(query_text=query_text, top_k=k)  # type: ignore
        )

        context_str = "\n".join([c.text for c in rag_resp.chunks])

        logger.info(
            f"Retrieved {len(rag_resp.chunks)} chunks. Context len: {len(context_str)}"
        )
        return rag_resp.chunks, context_str

    def get_answer_stream(self, query_text: str):
        if not query_text:
            return

        try:
            # 1. Retrieve Context
            yield service_pb2.ChatStreamResponse(event_type="thinking")  # type: ignore

            chunks, context_str = self._get_context(query_text)

            yield service_pb2.ChatStreamResponse(  # type: ignore
                context_chunks=chunks, event_type="context"
            )

            # 2. Stream LLM Answer
            logger.info("Starting LLM streaming response")
            llm_stream = self.llm_stub.StreamResponse(
                service_pb2.LLMRequest(  # type: ignore
                    user_query=query_text,
                    context=context_str,
                )
            )

            for chunk in llm_stream:
                yield service_pb2.ChatStreamResponse(  # type: ignore
                    text_chunk=chunk.text, event_type="answer"
                )

        except Exception as e:
            logger.error(f"Pipeline Stream Error: {e}")
            yield service_pb2.ChatStreamResponse(  # type: ignore
                text_chunk="I encountered an error processing your request.",
                event_type="error",
            )

    def get_answer_unary(self, query_text: str) -> service_pb2.ChatResponse: # type: ignore
        """
        Non-streaming version for the /chat endpoint.
        """
        try:
            chunks, context_str = self._get_context(query_text)  # type: ignore

            logger.info("Generating LLM response (Unary)")
            llm_resp = self.llm_stub.GenerateResponse(
                service_pb2.LLMRequest(user_query=query_text, context=context_str) # type: ignore
            )

            return service_pb2.ChatResponse(text=llm_resp.text, context_chunks=chunks)  # type: ignore
        except Exception as e:
            logger.error(f"Pipeline Unary Error: {e}")
            # Return empty or error response depending on proto definition
            return service_pb2.ChatResponse(text="Internal Error")  # type: ignore