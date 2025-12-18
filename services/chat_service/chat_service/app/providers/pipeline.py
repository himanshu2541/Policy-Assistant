import logging
import grpc
from chat_service.app.core.pipeline import FlexiblePipeline

from chat_service.app.core.steps import (
    ThinkingStep,
    RetrievalStep,
    GenerationStep,
)

from chat_service.app.adapters.grpc_adapters import (
    GrpcAnswerGenerator,
    GrpcContextRetriever,
)
from shared.protos import service_pb2_grpc
from shared.config import Config

logger = logging.getLogger("Chat-Service.Providers.Pipeline")


class PipelineFactory:
    """
    Factory to handle the complexity of gRPC channel creation.
    """

    @staticmethod
    def create(settings: Config) -> FlexiblePipeline:
        config = settings
        logger.info("Initializing RAG Pipeline connections...")

        # Helper to fix Docker networking issues (0.0.0.0 vs localhost)
        def get_target(host, port):
            if host == "0.0.0.0":
                host = "localhost"
            return f"{host}:{port}"

        # Create RAG Stub
        rag_target = get_target(config.RAG_SERVICE_HOST, config.RAG_SERVICE_PORT)
        rag_channel = grpc.insecure_channel(rag_target)
        rag_stub = service_pb2_grpc.RAGServiceStub(rag_channel)
        logger.info(f"Connected to RAG Service at {rag_target}")

        # Create LLM Stub
        llm_target = get_target(config.LLM_SERVICE_HOST, config.LLM_SERVICE_PORT)
        llm_channel = grpc.insecure_channel(llm_target)
        llm_stub = service_pb2_grpc.LLMServiceStub(llm_channel)
        logger.info(f"Connected to LLM Service at {llm_target}")

        # Create adapters
        retriever_adapter = GrpcContextRetriever(rag_stub, config)
        generator_adapter = GrpcAnswerGenerator(llm_stub)

        # Steps
        steps = [
            ThinkingStep(),
            RetrievalStep(retriever_adapter),
            GenerationStep(generator_adapter),
        ]

        # steps=[
        #     ThinkingStep(),
        #     SafetyCheckStep(), # New step injected easily
        #     RetrievalStep(retriever_adapter),
        #     GenerationStep(generator_adapter)
        # ]

        return FlexiblePipeline(steps=steps)
