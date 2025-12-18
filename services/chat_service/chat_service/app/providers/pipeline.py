import logging
import grpc
from chat_service.app.core.pipeline import RAGPipeline
from chat_service.app.adapters.grpc_adapters import (
    GrpcAnswerGenerator,
    GrpcContextRetriever,
)
from shared.protos import service_pb2_grpc
from shared.config import config

logger = logging.getLogger("Chat-Service.Providers.Pipeline")


class PipelineFactory:
    """
    Factory to handle the complexity of gRPC channel creation.
    """

    @staticmethod
    def create(config_instance=config) -> RAGPipeline:
        logger.info("Initializing RAG Pipeline connections...")

        # Helper to fix Docker networking issues (0.0.0.0 vs localhost)
        def get_target(host, port):
            if host == "0.0.0.0":
                host = "localhost"
            return f"{host}:{port}"

        # Create RAG Stub
        rag_target = get_target(
            config_instance.RAG_SERVICE_HOST, config_instance.RAG_SERVICE_PORT
        )
        rag_channel = grpc.insecure_channel(rag_target)
        rag_stub = service_pb2_grpc.RAGServiceStub(rag_channel)
        logger.info(f"Connected to RAG Service at {rag_target}")

        # Create LLM Stub
        llm_target = get_target(
            config_instance.LLM_SERVICE_HOST, config_instance.LLM_SERVICE_PORT
        )
        llm_channel = grpc.insecure_channel(llm_target)
        llm_stub = service_pb2_grpc.LLMServiceStub(llm_channel)
        logger.info(f"Connected to LLM Service at {llm_target}")

        # Create adapters
        retriever_adapter = GrpcContextRetriever(rag_stub, config_instance)
        generator_adapter = GrpcAnswerGenerator(llm_stub)

        return RAGPipeline(retriever_adapter, generator_adapter, config_instance)
