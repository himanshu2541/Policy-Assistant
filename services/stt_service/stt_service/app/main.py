import grpc
from concurrent import futures
from shared.config import config as settings, setup_logging
import logging

from .protos import stt_pb2_grpc, stt_pb2

setup_logging()
logger = logging.getLogger("stt_service")


class StreamingSTT(stt_pb2_grpc.STTServicer):
    def __init__(self, config_instance=settings):
        self.settings = config_instance

    async def Transcribe(self, request, context):
        audio_len = len(request.audio_content)
        text = f"Mock unary transcript ({audio_len} bytes) for {request.filename}"

        return stt_pb2.TranscriptionResponse(text=text, success=True, message="ok") # type: ignore

    async def TranscribeStream(self, request_iterator, context):
        config = None
        collected = bytearray()

        async for req in request_iterator:
            if req.HasField("config"):
                config = req.config
                print("Received config:", config)
                continue

            if req.HasField("audio"):
                collected.extend(req.audio.data)
                print("Received chunk:", len(req.audio.data))

                if config and config.return_partials:
                    yield stt_pb2.StreamResponse( # type: ignore
                        partial=stt_pb2.PartialTranscript( # type: ignore
                            text=f"(partial) received {len(collected)} bytes",
                            stability=0.9,
                        )
                    )

                if req.audio.is_last:
                    print("Last chunk received")
                    break

        final_text = f"Mock final transcript ({len(collected)} bytes) for {config.filename}" # type: ignore

        yield stt_pb2.StreamResponse( # type: ignore
            final=stt_pb2.FinalTranscript( # type: ignore
                text=final_text,
                success=True,
                message="ok"
            )
        )



async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=8))
    stt_pb2_grpc.add_STTServicer_to_server(StreamingSTT(), server)
    server.add_insecure_port(f"{settings.STT_HOST}:{settings.STT_PORT}")
    logger.info(
        f"STT streaming gRPC server listening on {settings.STT_HOST}:{settings.STT_PORT}"
    )
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())
