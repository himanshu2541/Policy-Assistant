import uvicorn
from shared.config import config

def run():
    uvicorn.run(
        "api_gateway.app.main:app",
        host=config.API_GATEWAY_HOST,
        port=int(config.API_GATEWAY_PORT),
        log_level=config.LOG_LEVEL,
        reload=config.RELOAD,
    )

if __name__ == "__main__":
    run()
