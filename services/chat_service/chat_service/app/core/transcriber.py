import logging
from typing import Iterable, Generator

import io
from shared.protos import service_pb2
from shared.config import Config

import speech_recognition as sr
from chat_service.app.interfaces import AudioStreamConverter, STTStrategy
from chat_service.app.providers.stt import STTFactory

logger = logging.getLogger("Chat-Service.Core.Transcriber")


class TranscriptionService:
    def __init__(self, converter: AudioStreamConverter, settings: Config):
        self.config = settings
        # 1. Inject the Converter (Adapter Pattern)
        self.converter = converter

        # 2. Load the Strategy (Factory Pattern)
        self.stt_strategy: STTStrategy = STTFactory.get_transcriber(self.config)

    def process_stream(self, request_iterator) -> Generator[service_pb2.ChatStreamResponse, None, None]: # type: ignore
        logger.info("Starting Batch Transcription...")

        # 1. Accumulate all chunks from the gRPC stream
        buffer = io.BytesIO()
        try:
            for request in request_iterator:
                if request.content:
                    buffer.write(request.content)
        except Exception as e:
            logger.error(f"Error receiving stream: {e}")
            return

        webm_data = buffer.getvalue()
        
        if not webm_data:
            logger.warning("Received empty audio stream.")
            return

        logger.info(f"Buffered {len(webm_data)} bytes. Converting...")

        try:
            # 2. Convert WebM -> WAV (Batch)
            wav_data = self.converter.convert_bytes(webm_data)
            
            # 3. Transcribe Once
            logger.info("Transcribing...")
            text = self.stt_strategy.transcribe(wav_data, self.config)

            if text and text.strip():
                logger.info(f"Final Transcription: {text}")
                # Yield the single final result
                yield service_pb2.ChatStreamResponse( # type: ignore
                    event_type="transcription", 
                    text_chunk=text
                )
            else:
                yield service_pb2.ChatStreamResponse( # type: ignore
                    event_type="error", 
                    text_chunk="No speech detected."
                )

        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            yield service_pb2.ChatStreamResponse( # type: ignore
                event_type="error", 
                text_chunk="Error processing audio."
            )