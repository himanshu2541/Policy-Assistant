import time
import re
import logging
from shared.protos import service_pb2
from chat_service.app.providers.stt import STTProvider

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self):
        logger.info("Initializing Transcription Service")
        self.stt = STTProvider()
        self.stt.get_instance()
        logger.info("STT provider initialized")
        self.transcribe_interval = 0.5

    def process_stream(self, request_iterator):
        """
        Smart Sliding Window:
        1. Accumulates Audio.
        2. Transcribes.
        3. If a sentence is finished, 'commits' it and clears audio buffer.
        4. Uses committed text as prompt for next chunk.
        """
        audio_buffer = bytearray()
        last_transcribe_time = 0

        committed_text = ""
        uncommitted_text = ""

        for chunk in request_iterator:
            audio_buffer.extend(chunk.content)
            yield service_pb2.ChatStreamResponse(event_type="listening")  # type: ignore

            current_time = time.time()
            if current_time - last_transcribe_time > self.transcribe_interval:

                # Transcribe current buffer using history as context
                # We pass 'committed_text' so Whisper knows what was said before!
                full_transcription = self._transcribe_with_prompt(
                    audio_buffer, prompt=committed_text
                )

                # Send update to UI (History + Current Flux)
                # Frontend sees the full smooth sentence
                yield service_pb2.ChatStreamResponse(  # type: ignore
                    text_chunk=f"{committed_text} {full_transcription}".strip(),
                    event_type="transcription",
                )

                # If we have a lot of audio (>5s) or a sentence ending,
                # we try to commit the stable part to keep the buffer small.
                if (
                    len(audio_buffer) > 16000 * 5
                ):  # Approx 5 seconds (16kHz * 2 bytes * 5)
                    stable_part, new_buffer_idx = self._find_stable_sentence(
                        full_transcription
                    )

                    if stable_part:
                        committed_text += f" {stable_part}"
                        # "Cut" the audio buffer (approximate mapping text -> audio is hard,
                        # so we only clear if we are fairly sure, or we clear everything)

                        # Ideally, we need word-level timestamps to cut audio accurately.
                        # For keeping it simple, we simply reset buffer IF we have a full pause/sentence.
                        # But blindly cutting audio bytes based on text is risky.

                        # In real apps
                        # Don't cut audio automatically. Just rely on the prompt context
                        # and rely on the user stopping talking to finish the request.
                        pass

                uncommitted_text = full_transcription
                last_transcribe_time = current_time

        final_part = self._transcribe_with_prompt(audio_buffer, prompt=committed_text)
        final_full_text = f"{committed_text} {final_part}".strip()

        return final_full_text

    def _transcribe_buffer(self, buffer: bytearray) -> str:
        if not buffer:
            return ""
        logger.info(f"Transcribing audio buffer of {len(buffer)} bytes")
        return self.stt.transcribe(bytes(buffer))

    def _transcribe_with_prompt(self, buffer: bytearray, prompt: str) -> str:
        if not buffer:
            return ""

        model = self.stt.get_instance()
        import io

        audio_file = io.BytesIO(bytes(buffer))

        segments, _ = model.transcribe(
            audio_file,
            beam_size=5,
            initial_prompt=prompt,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        return " ".join([segment.text for segment in segments]).strip()

    def _find_stable_sentence(self, text):
        """
        Helper to find sentence boundaries.
        Returns (stable_text, approximate_audio_cut_index)
        """
        # Regex for sentence endings
        match = re.search(r"([.?!])\s+", text)
        if match:
            end_idx = match.end()
            return text[:end_idx].strip(), -1
        return None, 0
