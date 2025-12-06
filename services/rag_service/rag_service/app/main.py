import grpc
import os
import time
import json
import logging
from concurrent import futures
from redis import Redis


from shared.providers.embeddings import EmbeddingsProvider
from shared.providers.vector_database import VectorDatabase
from shared.protos import service_pb2, service_pb2_grpc
from shared.config import setup_logging, config

setup_logging()
logger = logging.getLogger("RAG-Service")


class RAGService(service_pb2_grpc.RAGServiceServicer):
    def __init__(self, config_instance=config):
        self.config = config_instance
        logger.info("Initializing RAG Service components")
        # Redis Connection
        self.redis = Redis.from_url(self.config.REDIS_URL, decode_responses=True)
        logger.info("Redis connection established")

        # Initialize Providers
        # This loads the model (Local or OpenAI) once at startup
        self.embedding_provider = EmbeddingsProvider(self.config).get_embeddings()
        logger.info("Embedding provider initialized")

        # This connects to Pinecone using the embedding model
        self.vector_db = VectorDatabase(
            self.embedding_provider, self.config
        ).get_store()
        logger.info("Vector database connection established")

    def TriggerSync(self, request, context):
        """Queue job for worker."""
        job_payload = json.dumps(
            {"doc_id": request.doc_id, "file_path": request.file_path}
        )
        try:
            self.redis.lpush("rag_jobs", job_payload)
            job_id = f"job_{int(time.time())}"
            logger.info(f"Queued RAG job for doc_id: {request.doc_id}, job_id: {job_id}")
            return service_pb2.SyncResponse(status="Queued", job_id=job_id)  # type: ignore
        except Exception as e:
            logger.error(f"Redis Error: {e}")
            return service_pb2.SyncResponse(status="Failed")  # type: ignore

    def RetrieveContext(self, request, context):
        """Search Vector DB using LangChain."""
        try:
            logger.info(f"Performing similarity search for query: '{request.query_text}' with top_k: {request.top_k or 3}")
            # LangChain handles: Text -> Vector -> Pinecone Query -> Results
            results = self.vector_db.similarity_search_with_score(
                query=request.query_text, k=request.top_k or 5
            )

            # Build Response
            response = service_pb2.SearchResponse()  # type: ignore
            for doc, score in results:
                chunk = response.chunks.add()
                chunk.text = doc.page_content
                chunk.doc_id = doc.metadata.get("doc_id", "unknown")
                chunk.score = score

            logger.info(f"Search completed, found {len(results)} chunks")
            return response

        except Exception as e:
            logger.error(f"Search Error: {e}")
            return service_pb2.SearchResponse()  # type: ignore


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_RAGServiceServicer_to_server(RAGService(), server)
    port = config.RAG_SERVICE_PORT
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"RAG Service started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
