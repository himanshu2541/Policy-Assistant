import logging
import grpc
from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config

logger = logging.getLogger("chat_service.app.core.pipeline")

class RAGPipeline:
    def __init__(self, config_instance=config):
        self.config = config_instance
        self.rag_stub = service_pb2_grpc.RAGServiceStub(
            grpc.insecure_channel(
                f"{self.config.RAG_SERVICE_HOST}:{self.config.RAG_SERVICE_PORT}"
            )
        )
        self.llm_stub = service_pb2_grpc.LLMServiceStub(
            grpc.insecure_channel(
                f"{self.config.LLM_SERVICE_HOST}:{self.config.LLM_SERVICE_PORT}"
            )
        )

    def get_answer_stream(self, query_text: str):
        """
        Generator that handles RAG Retrieval -> LLM Streaming.
        Yields ChatStreamResponse.
        """
        if not query_text:
            return

        try:
            # 1. Retrieve Context
            yield service_pb2.ChatStreamResponse(event_type="thinking")  # type: ignore

            rag_resp = self.rag_stub.RetrieveContext(
                service_pb2.SearchRequest(query_text=query_text, top_k=3)  # type: ignore
            )
            context_str = "\n".join([c.text for c in rag_resp.chunks])
            logger.info(f"Found {len(rag_resp.chunks)} relevant chunks")

            # 2. Stream LLM Answer
            llm_stream = self.llm_stub.StreamResponse(
                service_pb2.LLMRequest(  # type: ignore
                    user_query=query_text,
                    context=context_str,
                    system_prompt="You are a helpful policy assistant.",
                )
            )

            for chunk in llm_stream:
                yield service_pb2.ChatStreamResponse(  # type: ignore
                    text_chunk=chunk.text, event_type="answer"
                )

        except Exception as e:
            logger.error(f"Pipeline Error: {e}")
            yield service_pb2.ChatStreamResponse(  # type: ignore
                text_chunk="I encountered an error processing your request.",
                event_type="error",
            )

    def get_answer_unary(self, query_text: str) -> service_pb2.ChatResponse:  # type: ignore
        """
        Non-streaming version for the /chat endpoint.
        """
        rag_resp = self.rag_stub.RetrieveContext(
            service_pb2.SearchRequest(query_text=query_text, top_k=3)  # type: ignore
        )
        context_str = "\n".join([c.text for c in rag_resp.chunks])

        llm_resp = self.llm_stub.GenerateResponse(
            service_pb2.LLMRequest(user_query=query_text, context=context_str)  # type: ignore
        )

        return service_pb2.ChatResponse(  # type: ignore
            text=llm_resp.text, context_chunks=rag_resp.chunks
        )
