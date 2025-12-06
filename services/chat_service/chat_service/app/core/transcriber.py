import time
import logging
from shared.protos import service_pb2
from chat_service.app.providers.stt import STTProvider

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self):
        self.stt = STTProvider()
        self.stt.get_instance()
        self.transcribe_interval = 0.5

    def process_stream(self, request_iterator):
        """
        Consumes audio stream and yields partial transcription updates.
        Returns the final transcription string after the generator is exhausted.
        """
        audio_buffer = bytearray()
        last_transcribe_time = 0.0
        final_text = ""

        # Loop through gRPC stream
        for chunk in request_iterator:
            audio_buffer.extend(chunk.content)

            # Send immediate "listening" feedback
            yield service_pb2.ChatStreamResponse(event_type="listening")  # type: ignore

            current_time = time.time()
            if current_time - last_transcribe_time > self.transcribe_interval:
                partial_text = self._transcribe_buffer(audio_buffer)
                if partial_text:
                    final_text = partial_text  # Update our tracking var
                    yield service_pb2.ChatStreamResponse(  # type: ignore
                        text_chunk=partial_text, event_type="transcription"
                    )
                last_transcribe_time = current_time

        # Final Transcription on full buffer
        final_text = self._transcribe_buffer(audio_buffer)

        return final_text

    def _transcribe_buffer(self, buffer: bytearray) -> str:
        if not buffer:
            return ""
        return self.stt.transcribe(bytes(buffer))
