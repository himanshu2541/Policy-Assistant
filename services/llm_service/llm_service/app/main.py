import grpc
import logging
from concurrent import futures

from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config, setup_logging
from llm_service.app.providers.chain import ChainProvider

setup_logging()
logger = logging.getLogger("LLM-Service")

class LLMService(service_pb2_grpc.LLMServiceServicer):
    def __init__(self, config_instance=config):
        self.config = config_instance
        self.chain_provider = ChainProvider(self.config)

    def GenerateResponse(self, request, context):
        try:
            logger.info(f"Generating for: {request.user_query[:20]}...")
            
            # 1. Get the Chain
            chain = self.chain_provider.create_chain(request.system_prompt)
            
            # 2. Run the Chain
            # We map the gRPC request fields to the Prompt variables
            result_text = chain.invoke({
                "context": request.context,
                "input": request.user_query
            })
            
            return service_pb2.LLMResponse(text=result_text) # type: ignore

        except Exception as e:
            logger.error(f"Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.LLMResponse() # type: ignore

    def StreamResponse(self, request, context):
        try:
            logger.info(f"Streaming for: {request.user_query[:20]}...")
            
            # 1. Get the Chain
            chain = self.chain_provider.create_chain(request.system_prompt)
            
            # 2. Stream the Chain
            for token in chain.stream({
                "context": request.context,
                "input": request.user_query
            }):
                yield service_pb2.LLMResponse(text=token) # type: ignore
                
        except Exception as e:
            logger.error(f"Stream Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    port = config.LLM_SERVICE_PORT
    server.add_insecure_port(f'{config.LLM_SERVICE_HOST}:{port}')
    logger.info(f"LLM Service started on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()