import uvicorn
from shared.config import config as settings

def run():
    uvicorn.run(
        "query_service.app.main:app",
        host=settings.QUERY_HOST,
        port=int(settings.QUERY_PORT),
        log_level=settings.LOG_LEVEL,
        reload=settings.RELOAD,
    )

if __name__ == "__main__":
    run()
