import logging
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    OPENAI_API_KEY: str = ""

    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    REDIS_URL: str = "redis://localhost:6379/0"

    QUERY_HOST: str = ""
    QUERY_PORT: int = 8001
    INGEST_HOST: str = ""
    INGEST_PORT: int = 8002
    STT_HOST: str = ""
    STT_PORT: int = 50051

    CHAT_SERVICE_HOST: str = "0.0.0.0"
    CHAT_SERVICE_PORT: int = 50052
    RAG_SERVICE_HOST: str = "0.0.0.0"
    RAG_SERVICE_PORT: int = 50053
    LLM_SERVICE_HOST: str = "0.0.0.0"
    LLM_SERVICE_PORT: int = 50054
    API_GATEWAY_HOST: str = "0.0.0.0"
    API_GATEWAY_PORT: int = 8000

    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # Options: "openai" or "local" (for LM Studio/Ollama)
    LLM_PROVIDER: str = "local"
    LLM_MODEL: str = "phi-3-mini-4k-instruct"
    LLM_BASE_URL: str = "http://localhost:1234/v1"
    LLM_TEMPERATURE: float = 0.8

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = ""

    STT_MODEL_SIZE: str = "small"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"

    RELOAD: bool = True if ENV == "development" else False
    UPLOAD_DIR: str = "/data/uploads"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     extra = "ignore"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def setup_logging():
    """
    Configures the root logger for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


config = Config()
