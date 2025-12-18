import logging
from shared.interfaces import StorageProvider
from shared.providers.storage import LocalStorageProvider
from shared.providers.redis import RedisFactory
from shared.config import config

from api_gateway.services.chat_client import ChatServiceClient

logger = logging.getLogger("API-Gateway.Core.Dependencies")


async def get_redis_connection():
    """
    Dependency that yields a Redis connection from the pool.
    Usage: redis = Depends(get_redis_connection)
    """
    client = RedisFactory.get_client(config)
    yield client


async def get_redis_pubsub():
    """Helper to get a raw connection for PubSub"""
    return RedisFactory.get_client(config)


def get_storage_service() -> StorageProvider:
    """
    Returns the configured StorageProvider.
    To switch to change the logic here.
    """
    # Example logic for future switching:
    # if config.STORAGE_TYPE == "s3":
    #     return S3StorageProvider(bucket=config.S3_BUCKET)

    return LocalStorageProvider(upload_dir=config.UPLOAD_DIR)


def get_chat_client():
    """
    Returns an instance of ChatServiceClient.
    Usage: chat_client = Depends(get_chat_client)
    """
    return ChatServiceClient(settings=config)
