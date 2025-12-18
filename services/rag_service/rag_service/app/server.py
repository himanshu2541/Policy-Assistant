import grpc
import logging
from concurrent import futures
from shared.protos import service_pb2_grpc
from shared.config import config
from rag_service.app.service import RAGService

logger = logging.getLogger("RAG-Service.App.Server")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_RAGServiceServicer_to_server(RAGService(settings=config), server)
    
    port = config.RAG_SERVICE_PORT
    server.add_insecure_port(f"[::]:{port}")
    
    logger.info(f"RAG Service running on port {port}")
    server.start()
    server.wait_for_termination()