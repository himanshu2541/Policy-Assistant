import logging
import sys
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    ENV: str = "development" 
    LOG_LEVEL: str = "INFO"

    QUERY_HOST: str = ""
    QUERY_PORT: int = 8001
    INGEST_HOST: str = ""
    INGEST_PORT: int = 8002
    STT_HOST: str = ""
    STT_PORT: int = 50051

    VECTOR_DB_URL: str = ""
    VECTOR_DB_URL: str = ""

    RELOAD: bool = True if ENV == "development" else False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

def setup_logging():
    """
    Configures the root logger for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


config = Config()
