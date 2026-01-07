import logging
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    OPENAI_API_KEY: str = ""

    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    REDIS_URL: str = "redis://localhost:6379/0"

    CHAT_SERVICE_HOST: str = "localhost"
    CHAT_SERVICE_PORT: int = 50051

    RAG_SERVICE_HOST: str = "localhost"
    RAG_SERVICE_PORT: int = 50052

    LLM_SERVICE_HOST: str = "localhost"
    LLM_SERVICE_PORT: int = 50053
    
    API_GATEWAY_HOST: str = "0.0.0.0"
    API_GATEWAY_PORT: int = 8000

    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5

    # Retrieval Strategy Configuration
    # Options: "ensemble", "dense", "mmr"
    RETRIEVAL_STRATEGY: str = "ensemble"
    # New: Weights for Ensemble [Dense, MMR]
    RETRIEVAL_WEIGHTS: List[float] = [0.6, 0.4]

    # Options: "openai" or "local" (for LM Studio/Ollama)
    LLM_PROVIDER: str = "local"
    LLM_MODEL: str = "mistral-7b-instruct-v0.3"
    LLM_BASE_URL: str = "http://localhost:1234/v1"
    LLM_TEMPERATURE: float = 0.0

    VECTOR_DB_PROVIDER: str = "pinecone"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = ""

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    STT_PROVIDER: str = "local"  # "local" or "openai"
    STT_MODEL_SIZE: str = "small"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"

    RELOAD: bool = True if ENV == "development" else False
    UPLOAD_DIR: str = "./data/uploads"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


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