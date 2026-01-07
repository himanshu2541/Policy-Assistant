import time
import json
import logging
import asyncio

from shared.protos import service_pb2, service_pb2_grpc
from shared.config import Config

from rag_service.components.graph_retriever import GraphRetriever
from rag_service.components.search_engine import SearchEngine
from rag_service.core.dependencies import get_vector_store

from shared.providers.llm import LLMFactory
from shared.providers.neo4j_client import Neo4jClient
from shared.providers.redis import RedisFactory

logger = logging.getLogger("RAG-Service.App.Service")


class RAGService(service_pb2_grpc.RAGServiceServicer):
    def __init__(self, settings: Config):
        self.config = settings
        logger.info("Initializing RAG Service components")

        self.redis = RedisFactory.get_client(self.config)

        vector_store_adapter = get_vector_store()
        # Search Engine for Retrieval
        self.search_engine = SearchEngine(vector_store_adapter, self.config)

        self.neo4j_client = Neo4jClient.get_instance()
        self.llm = LLMFactory.get_llm(self.config)
        self.graph_retriever = GraphRetriever(self.neo4j_client, self.llm)

    async def RetrieveContext(self, request, context):
        try:
            loop = asyncio.get_running_loop()
            
            # Prepare Parallel Tasks
            # We use run_in_executor because search_engine and graph_retriever 
            # likely use blocking I/O (Requests/Socket)
            
            vector_task = loop.run_in_executor(
                None, 
                lambda: self.search_engine.search(
                    query=request.query_text, 
                    top_k=request.top_k or 5
                )
            )

            graph_task = loop.run_in_executor(
                None,
                lambda: self.graph_retriever.get_context(request.query_text)
            )

            # Execute concurrently
            vector_results, graph_context_str = await asyncio.gather(vector_task, graph_task)

            # Build Response
            response = service_pb2.SearchResponse()  # type: ignore
            
            # Add Vector Chunks
            for doc in vector_results:
                chunk = response.chunks.add()
                chunk.text = doc.page_content
                chunk.doc_id = doc.metadata.get("doc_id", "unknown")
                chunk.score = 1.0 # Placeholder score

            # Add Graph Chunk (if content found)
            if graph_context_str:
                chunk = response.chunks.add()
                chunk.text = f"--- GRAPH KNOWLEDGE ---\n{graph_context_str}"
                chunk.doc_id = "graph_retrieval"
                chunk.score = 1.0

            logger.info(
                f"Retrieved {len(vector_results)} vector docs and graph context for: '{request.query_text}'"
            )
            return response
            
        except Exception as e:
            logger.error(f"Search Error: {e}")
            return service_pb2.SearchResponse()  # type: ignore

    async def TriggerSync(self, request, context):
        job_payload = json.dumps(
            {"doc_id": request.doc_id, "file_path": request.file_path}
        )
        try:
            await self.redis.lpush("rag_jobs", job_payload) # type: ignore
            job_id = f"job_{int(time.time())}"
            logger.info(
                f"Queued RAG job for doc_id: {request.doc_id}, job_id: {job_id}"
            )
            return service_pb2.SyncResponse(status="Queued", job_id=job_id)  # type: ignore
        except Exception as e:
            logger.error(f"Redis Error: {e}")
            return service_pb2.SyncResponse(status="Failed")  # type: ignore

    async def ListDocuments(self, request, context):
        """Fetch all documents from Redis metadata store."""
        try:
            raw_data = await self.redis.hgetall("rag_documents") # type: ignore

            docs = []
            for doc_id, json_str in raw_data.items():  # type: ignore
                data = json.loads(json_str)
                docs.append(
                    service_pb2.DocumentMetadata(  # type: ignore
                        doc_id=data.get("doc_id"),
                        filename=data.get("filename"),
                        status=data.get("status"),
                        timestamp=data.get("timestamp"),
                    )
                )

            return service_pb2.ListDocsResponse(docs=docs)  # type: ignore
        except Exception as e:
            logger.error(f"List Docs Error: {e}")
            return service_pb2.ListDocsResponse()  # type: ignore

    async def DeleteVectors(self, request, context):
        try:
            success = self.search_engine.delete_vector(request.doc_id)

            if success:
                logger.info(f"Vectors deleted for doc_id: {request.doc_id}")
                await self.redis.hdel("rag_documents", request.doc_id) # type: ignore
            logger.info(
                f"Deleted vectors for doc_id: {request.doc_id}, success: {success}"
            )
            return service_pb2.DeleteVectorResponse(success=success)  # type: ignore
        except Exception as e:
            logger.error(f"Delete Error: {e}")
            return service_pb2.DeleteVectorResponse(success=False)  # type: ignore