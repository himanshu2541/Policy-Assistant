import logging
from typing import List, Tuple, Generator, Any
from shared.protos import service_pb2
from shared.config import Config
from chat_service.app.interfaces import ContextRetriever, AnswerGenerator

logger = logging.getLogger("Chat-Service.Adapters.Grpc")

class GrpcContextRetriever(ContextRetriever):
    """
    Implementation of ContextRetriever that calls the RAG Service via gRPC.
    """
    def __init__(self, rag_stub, config: Config):
        self.rag_stub = rag_stub
        self.config = config

    def retrieve(self, query: str) -> Tuple[List[Any], str]:
        logger.info(f"Retrieving context for: '{query[:50]}...'")
        k = getattr(self.config, "RAG_TOP_K", 3)
        
        # Call gRPC Service
        req = service_pb2.SearchRequest(query_text=query, top_k=k) # type: ignore
        rag_resp = self.rag_stub.RetrieveContext(req)
        
        context_str = "\n".join([c.text for c in rag_resp.chunks])
        logger.info(f"Retrieved {len(rag_resp.chunks)} chunks.")
        
        return rag_resp.chunks, context_str

class GrpcAnswerGenerator(AnswerGenerator):
    """
    Implementation of AnswerGenerator that calls the LLM Service via gRPC.
    """
    def __init__(self, llm_stub):
        self.llm_stub = llm_stub

    def generate_response(self, query: str, context: str) -> str:
        req = service_pb2.LLMRequest(user_query=query, context=context) # type: ignore
        llm_resp = self.llm_stub.GenerateResponse(req)
        return llm_resp.text

    def stream_response(self, query: str, context: str) -> Generator[str, None, None]:
        req = service_pb2.LLMRequest(user_query=query, context=context) # type: ignore
        llm_stream = self.llm_stub.StreamResponse(req)
        
        for chunk in llm_stream:
            yield chunk.text