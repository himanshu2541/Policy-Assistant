import uvicorn
from shared.config import config as settings


def run():
    uvicorn.run(
        "ingestion_service.app.main:app",
        host=settings.INGEST_HOST,
        port=int(settings.INGEST_PORT),
        log_level=settings.LOG_LEVEL,
        reload=settings.RELOAD,
    )


if __name__ == "__main__":
    run()
