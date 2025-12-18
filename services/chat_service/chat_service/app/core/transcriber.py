import logging
from typing import Iterable
from shared.protos import service_pb2
from chat_service.app.providers.stt import STTFactory
from shared.config import Config

logger = logging.getLogger("Chat-Service.Core.Transcriber")


class TranscriptionService:
    def __init__(self, settings: Config):
        self.config = settings
        self.stt_strategy = STTFactory.get_transcriber(self.config)

        # Safety guards
        self.MIN_BYTES = 4000  # ~15 sec at 32kbps; below this is likely noise/silence
        self.MAX_BUFFER_BYTES = 1_000_000  # ~4–5 min at 32kbps; hard cap if needed

    def process_stream(self, request_iterator: Iterable):
        """
        Single-shot transcription:
        - Accumulate all audio bytes while client is speaking.
        - When stream ends, transcribe once and return full text.
        """
        audio_buffer = bytearray()

        logger.info("Starting Audio Stream Processing...")
        count = 0
        for chunk in request_iterator:
            count += 1
            # Log the first few chunks to verify data is arriving
            if count < 5:
                logger.info(f"Received chunk {count}: {len(chunk.content)} bytes")

        for chunk in request_iterator:
            if not getattr(chunk, "content", None):
                continue

            audio_buffer.extend(chunk.content)

            # Optional safety: stop accumulating if something goes wrong client-side
            if len(audio_buffer) > self.MAX_BUFFER_BYTES:
                # Truncate or break. Here: break.
                break

            # Inform the client that we are actively listening
            yield service_pb2.ChatStreamResponse(event_type="listening")  # type: ignore

        # End of stream
        if len(audio_buffer) < self.MIN_BYTES:
            # Very little or no audio: return empty result
            yield service_pb2.ChatStreamResponse(  # type: ignore
                text_chunk="",
                event_type="transcription",
            )
            return ""

        full_text = self._transcribe_full(audio_buffer)

        # Send final transcript to client
        yield service_pb2.ChatStreamResponse(  # type: ignore
            text_chunk=full_text,
            event_type="transcription",
        )

        # For server-side use; gRPC ignores this for streaming responses
        return full_text

    def _transcribe_full(self, audio_data: bytearray) -> str:
        """
        Collects all of the byetes and performs a single transcription.
        """
        temp_filename = ""
        if not audio_data:
            return ""

        try:
            return self.stt_strategy.transcribe(bytes(audio_data), self.config)

        except Exception as e:
            logger.error(f"[STT] Error in full transcription: {e}")
            return ""
