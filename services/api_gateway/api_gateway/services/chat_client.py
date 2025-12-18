import grpc
import logging
from typing import AsyncGenerator
from shared.protos import service_pb2, service_pb2_grpc
from shared.config import Config

logger = logging.getLogger("API-Gateway.Services.ChatClient")


class ChatServiceClient:
    """
    Abstracts the gRPC communication with the Chat Service.
    """

    def __init__(self, settings: Config):

        host = settings.CHAT_SERVICE_HOST
        port = settings.CHAT_SERVICE_PORT

        self.target = f"{host}:{port}"

    async def send_text_query(self, query: str, session_id: str) -> service_pb2.ChatResponse:  # type: ignore
        async with grpc.aio.insecure_channel(self.target) as channel:
            stub = service_pb2_grpc.ChatServiceStub(channel)
            try:
                request = service_pb2.ChatRequest(user_query=query, session_id=session_id)  # type: ignore
                return await stub.Interact(request)
            except grpc.RpcError as e:
                logger.error(f"gRPC Interact Error: {e.details()}")
                raise

    async def stream_audio_chat(
        self, request_iterator: AsyncGenerator
    ) -> AsyncGenerator:
        """
        :param request_iterator: A generator yielding AudioChunk messages
        :return: A generator yielding ChatStreamResponse messages
        """
        async with grpc.aio.insecure_channel(self.target) as channel:
            stub = service_pb2_grpc.ChatServiceStub(channel)
            try:
                # Forward the generator to the stub
                async for response in stub.StreamAudioChat(request_iterator):
                    yield response
            except grpc.RpcError as e:
                logger.error(f"gRPC Stream Error: {e.details()}")
                raise
