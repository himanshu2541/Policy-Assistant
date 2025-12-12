from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from api_gateway.app.routes import chat, upload, admin

import logging
from shared.config import setup_logging
setup_logging()
logger = logging.getLogger("API-Gateway.Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up API Gateway...")
    yield
    logger.info("Shutting down API Gateway...")


app = FastAPI(
    title="Policy Assistant API Gateway",
    version="1.0.0",
    description="API Gateway for the Policy Assistant application.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/", tags=["Root"])
async def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to the Policy Assistant API Gateway!"}


@app.get("/health", tags=["Health"])
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok"}
