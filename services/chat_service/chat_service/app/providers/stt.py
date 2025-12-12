import logging
import io
from faster_whisper import WhisperModel

from shared.config import config

logger = logging.getLogger("Chat-Service.Providers.STT")

class STTProvider:
    """
    Wrapper for Faster-Whisper.
    """

    def __init__(self, config_instance = config):
        self.config = config_instance

    _model_instance = None

    @classmethod
    def get_instance(cls):
        if cls._model_instance is None:
            logger.info(f"Loading Faster-Whisper model: {config.STT_MODEL_SIZE}...")
            cls._model_instance = WhisperModel(
                config.STT_MODEL_SIZE, 
                device=config.STT_DEVICE, 
                compute_type=config.STT_COMPUTE_TYPE
            )
            logger.info("STT Model loaded.")
        return cls._model_instance

    def transcribe(self, audio_bytes: bytes) -> str:
        model = self.get_instance()
        audio_buffer = io.BytesIO(audio_bytes)
        
        segments, info = model.transcribe(
            audio_buffer, 
            beam_size=5,
            vad_filter=True, 
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        return " ".join([segment.text for segment in segments]).strip()