import grpc
import logging
from concurrent import futures
from chat_service.app.core.pipeline import RAGPipeline
from shared.config import setup_logging, config
from shared.protos import service_pb2, service_pb2_grpc

from chat_service.app.core.transcriber import TranscriptionService
from chat_service.app.providers.pipeline import PipelineFactory

setup_logging()
logger = logging.getLogger("Chat-Service.Main")


class ChatService(service_pb2_grpc.ChatServiceServicer):
    def __init__(self, pipeline: RAGPipeline, config_instance=config):
        self.config = config_instance
        self.transcriber = TranscriptionService()
        self.pipeline = pipeline

    def Interact(self, request, context):
        """Standard Text Request"""
        logger.info(f"Text Query: {request.user_query}")
        try:
            return self.pipeline.get_answer_unary(request.user_query)
        except Exception as e:
            logger.error(f"Interact Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return service_pb2.ChatResponse()  # type: ignore

    def StreamAudioChat(self, request_iterator, context):
        """Voice Stream Request"""
        logger.info("Starting Audio Stream...")

        try:
            # 1. Consume Audio Stream (Yields "listening" and "transcription" events)
            # The 'process_stream' is a generator, so we iterate over it to send UI updates.
            # However, we need the RETURN value (final text) when it finishes.

            # Use 'yield from' if we didn't need the return value.
            # Since we do, we iterate manually.
            transcription_gen = self.transcriber.process_stream(request_iterator)

            final_text = ""
            for response in transcription_gen:
                yield response
                # Keep track of text updates to ensure we have the latest
                if response.event_type == "transcription":
                    final_text = response.text_chunk

            logger.info(f"Final Transcription: {final_text}")

            if not final_text.strip():
                yield service_pb2.ChatStreamResponse(  # type: ignore
                    event_type="error", text_chunk="No speech detected."
                )
                return

            # 2. Handover to RAG Pipeline (Yields "thinking" and "answer" events)
            yield from self.pipeline.get_answer_stream(final_text)

            # 3. Finish
            yield service_pb2.ChatStreamResponse(event_type="done")  # type: ignore

        except Exception as e:
            logger.error(f"Stream Error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pipeline = PipelineFactory.create(config)
    service_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(pipeline, config), server)

    port = config.CHAT_SERVICE_PORT
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Chat Service started on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
