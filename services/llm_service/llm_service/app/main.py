import grpc
import logging
from concurrent import futures

from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config, setup_logging, Config
from llm_service.app.providers.chain import ChainProvider

setup_logging()
logger = logging.getLogger("LLM-Service")


class LLMService(service_pb2_grpc.LLMServiceServicer):
    def __init__(self, chain_provider: ChainProvider, settings: Config):
        self.config = settings
        self.chain_provider = chain_provider
        logger.info("LLM Service initialized with dependencies")

    def _get_chain(self, request):
        """
        Helper to extract strategy and create the chain.
        Centralizes the default logic and creation call.
        Raises ValueError if strategy is unknown (handled by callers).
        """
        strategy = getattr(request, "strategy", "policy_chat") or "policy_chat"
        
        return self.chain_provider.create_chain(
            system_prompt=request.system_prompt,
            strategy_type=strategy
        )
    
    def GenerateResponse(self, request, context):
        try:
            logger.info(f"Generating response for: {request.user_query[:20]}...")

            # 1. Get the Chain
            chain = self._get_chain(request)
            logger.info("Chain created for generation")

            # 2. Run the Chain
            # We map the gRPC request fields to the Prompt variables
            result_text = chain.invoke(
                {"context": request.context, "input": request.user_query}
            )
            logger.info("Chain invoked successfully")

            return service_pb2.LLMResponse(text=result_text)  # type: ignore

        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.LLMResponse()  # type: ignore

    def StreamResponse(self, request, context):
        try:
            logger.info(f"Streaming response for: {request.user_query[:20]}...")

            # 1. Get the Chain
            chain = self._get_chain(request)
            logger.info("Chain created for streaming")

            # 2. Stream the Chain
            logger.info("Starting token streaming")
            for token in chain.stream(
                {"context": request.context, "input": request.user_query}
            ):
                yield service_pb2.LLMResponse(text=token)  # type: ignore

        except Exception as e:
            logger.error(f"Stream Error: {e}")
            print(f"Stream Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)


def serve():
    logger.info("Initializing dependencies...")
    chain_provider = ChainProvider(config)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    service = LLMService(chain_provider=chain_provider, settings=config)

    service_pb2_grpc.add_LLMServiceServicer_to_server(service, server)

    port = config.LLM_SERVICE_PORT
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"LLM Service started on port {port}")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
