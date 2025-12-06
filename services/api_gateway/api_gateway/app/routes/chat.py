from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import grpc
from api_gateway.app.models.chat import ChatRequest, ChatResponse
from api_gateway.app.models.document import DocumentContext

from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Standard text chat. API Gateway -> Chat Service (gRPC)
    """

    logger.info(f"Received chat request: {request}")

    try:
        async with grpc.aio.insecure_channel(config.CHAT_SERVICE_HOST) as channel:
            stub = service_pb2_grpc.ChatServiceStub(channel)  # type: ignore

            # Assuming ChatService has a generic 'Interact' or 'Generate' method
            # Might need to adjust based on exact proto definition
            grpc_req = service_pb2.ChatRequest(  # type: ignore
                user_query=request.query, session_id=request.session_id
            )

            response = await stub.Interact(grpc_req)

            formatted_context = [
                DocumentContext(
                    page_content=chunk.text,
                    metadata={
                        "doc_id": chunk.doc_id,
                        "score": chunk.score,
                    },
                )
                for chunk in response.context_chunks
            ]
            return ChatResponse(answer=response.text, contexts=formatted_context)

    except grpc.RpcError as e:
        logger.error(f"gRPC Chat Service error: {e.details()}")
        raise HTTPException(
            status_code=500, detail=f"Chat Service Error: {e.details()}"
        )


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    Receives Audio Stream (WebM) from browser, forwards to Chat Service via gRPC.
    """
    await websocket.accept()
    try:
        # Connect to Chat Service
        async with grpc.aio.insecure_channel(config.CHAT_SERVICE_HOST) as channel:
            stub = service_pb2_grpc.ChatServiceStub(channel)  # type: ignore

            # Define an iterator to yield audio chunks from WebSocket to gRPC
            async def request_generator():
                try:
                    while True:
                        # Receive bytes from browser
                        data = await websocket.receive_bytes()
                        # Yield to gRPC stream
                        yield service_pb2.AudioChunk(content=data)  # type: ignore
                except WebSocketDisconnect:
                    return

            # Call the Bidirectional Streaming RPC
            # API Gateway acts as a proxy: Browser Audio -> Gateway -> gRPC -> Gateway -> Browser Text
            async for response in stub.StreamAudioChat(request_generator()):
                # Send text updates back to frontend as they arrive
                await websocket.send_json(
                    {"text": response.text_chunk, "event": "transcription"}
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket (ws/chat) Error: {e}")
        await websocket.close()
