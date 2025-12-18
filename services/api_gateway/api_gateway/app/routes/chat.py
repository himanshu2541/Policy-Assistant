from fastapi import APIRouter, Depends, HTTPException, WebSocket
from api_gateway.app.models.chat import ChatRequest, ChatResponse
from api_gateway.app.models.document import DocumentContext

from api_gateway.core.dependencies import get_chat_client
from api_gateway.services.chat_client import ChatServiceClient

import logging
logger = logging.getLogger("API-Gateway.Routes.Chat")

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    request: ChatRequest, chat_client: ChatServiceClient = Depends(get_chat_client)
):
    """
    Standard text chat. API Gateway -> Chat Service (gRPC)
    """

    logger.info(f"Received chat request: {request}")

    try:
        response = await chat_client.send_text_query(request.query, request.session_id)

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

    except Exception as e:
        logger.error(f"Chat Service error: {e}")
        print(f"Chat Service error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat Service Error: {e}")


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket, chat_client: ChatServiceClient = Depends(get_chat_client)
):
    """
    Handles bidirectional audio streaming.
    Frontend sends: Binary Audio Chunks -> Then "END" string.
    Backend sends: JSON events {"text": "...", "event": "..."}
    """
    await websocket.accept()

    # 1. Define Producer (WebSocket -> gRPC)
    async def request_generator():
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    yield service_pb2.AudioChunk(content=message["bytes"], session_id="default")  # type: ignore
                elif "text" in message and message["text"] == "END":
                    break
        except Exception:
            pass  # Handle disconnects gracefully

    # 2. Consume & Forward (gRPC -> WebSocket)
    try:
        async for response in chat_client.stream_audio_chat(request_generator()):
            contexts_data = [
                {"text": c.text, "doc_id": c.doc_id, "score": c.score}
                for c in response.context_chunks
            ]
            await websocket.send_json(
                {
                    "text": response.text_chunk,
                    "event": response.event_type,
                    "contexts": contexts_data,
                }
            )
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        try:
            await websocket.send_json(
                {"error": "Service unavailable", "event": "error"}
            )
        except:
            pass
    finally:
        logger.info("WebSocket connection closed")
