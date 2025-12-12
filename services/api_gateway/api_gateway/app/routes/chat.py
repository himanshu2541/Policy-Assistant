from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import grpc
from api_gateway.app.models.chat import ChatRequest, ChatResponse
from api_gateway.app.models.document import DocumentContext

from shared.protos import service_pb2, service_pb2_grpc
from shared.config import config

import logging
import asyncio

logger = logging.getLogger("API-Gateway.Routes.Chat")

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Standard text chat. API Gateway -> Chat Service (gRPC)
    """

    logger.info(f"Received chat request: {request}")

    target = f"{config.CHAT_SERVICE_HOST}:{config.CHAT_SERVICE_PORT}"
    try:
        async with grpc.aio.insecure_channel(target) as channel:
            stub = service_pb2_grpc.ChatServiceStub(channel)  # type: ignore

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
        logger.error(f"gRPC Status Code: {e.code()}")
        logger.error(f"gRPC Debug Info: {e.debug_error_string()}")  # type: ignore
        logger.error(f"gRPC Chat Service error: {e.details()}")
        raise HTTPException(
            status_code=500, detail=f"Chat Service Error: {e.details()}"
        )


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles bidirectional audio streaming.
    Frontend sends: Binary Audio Chunks -> Then "END" string.
    Backend sends: JSON events {"text": "...", "event": "..."}
    """
    await websocket.accept()

    target = f"{config.CHAT_SERVICE_HOST}:{config.CHAT_SERVICE_PORT}"

    try:
        async with grpc.aio.insecure_channel(target) as channel:
            stub = service_pb2_grpc.ChatServiceStub(channel)

            # Define the Request Generator (The "Producer")
            # This reads from WebSocket and yields to gRPC
            async def request_generator():
                try:
                    while True:
                        # Use receive() to handle both bytes (Audio) and text ("END")
                        message = await websocket.receive()

                        if "bytes" in message:
                            # Audio Chunk
                            yield service_pb2.AudioChunk(  # type: ignore
                                content=message["bytes"], session_id="default"
                            )

                        elif "text" in message:
                            # Control Signal
                            text = message["text"]
                            if text == "END":
                                logger.info(
                                    "Received END signal from client. Closing stream."
                                )
                                break  # Stop yielding, which closes the gRPC Request Stream

                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                except Exception as e:
                    logger.error(f"Error in request_generator: {e}")

            # Consume the gRPC Response Stream (The "Consumer")
            # This waits for the Chat Service to send back updates
            async for response in stub.StreamAudioChat(request_generator()):
                try:
                    contexts_data = []
                    if response.context_chunks:
                        contexts_data = [
                            {"text": c.text, "doc_id": c.doc_id, "score": c.score}
                            for c in response.context_chunks
                        ]
                    # Send text updates back to frontend
                    await websocket.send_json(
                        {
                            "text": response.text_chunk,
                            "event": response.event_type,  # "transcription", "answer", etc.
                            "contexts": contexts_data,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to send to websocket: {e}")
                    break

    except asyncio.CancelledError:
        logger.info("Task cancelled (Client disconnected)")
        # No action needed, just exit cleanly
    except grpc.RpcError as e:
        logger.error(f"gRPC Error: {e.details()}")
        try:
            await websocket.send_json(
                {"error": "Voice service unavailable", "event": "error"}
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected WebSocket Error: {e}")
    finally:
        logger.info("WebSocket connection closed")
