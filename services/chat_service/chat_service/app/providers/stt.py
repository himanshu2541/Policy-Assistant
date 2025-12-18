import io
import logging
from shared.config import Config, config as global_config
from chat_service.app.interfaces import STTStrategy

logger = logging.getLogger("Shared.STT")

class FasterWhisperStrategy(STTStrategy):
    _model = None

    def _get_model(self, settings: Config):
        # Singleton Pattern for the Heavy Model
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Faster-Whisper: {settings.STT_MODEL_SIZE}")
            self._model = WhisperModel(
                settings.STT_MODEL_SIZE, 
                device=settings.STT_DEVICE, 
                compute_type=settings.STT_COMPUTE_TYPE
            )
        return self._model

    def transcribe(self, audio_bytes: bytes, settings: Config) -> str:
        model = self._get_model(settings)
        audio_buffer = io.BytesIO(audio_bytes)
        
        segments, info = model.transcribe(
            audio_buffer, 
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        return " ".join([segment.text for segment in segments]).strip()

class OpenAIWhisperStrategy(STTStrategy):
    def transcribe(self, audio_bytes: bytes, settings: Config) -> str:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        audio_buffer = io.BytesIO(audio_bytes)
        audio_buffer.name = "audio.wav" # OpenAI API needs a filename
        
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_buffer
        )
        return transcript.text

class STTFactory:
    _strategies = {
        "local": FasterWhisperStrategy(),
        "openai": OpenAIWhisperStrategy()
    }

    @classmethod
    def get_transcriber(cls, settings: Config = global_config) -> STTStrategy:
        provider = getattr(settings, "STT_PROVIDER", "local").lower()
        
        strategy = cls._strategies.get(provider)
        if not strategy:
            raise ValueError(f"Unknown STT Provider: {provider}")
            
        return strategy