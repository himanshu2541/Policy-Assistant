import logging
from redis import asyncio as aioredis
from shared.config import config

logger = logging.getLogger("API-Gateway")

_redis_pool = None

async def get_redis_connection():
    """
    Dependency that yields a Redis connection from the pool.
    Usage: redis = Depends(get_redis_connection)
    """
    global _redis_pool
    if _redis_pool is None:
        logger.info("Initializing Async Redis Pool...")
        _redis_pool = aioredis.from_url(
            config.REDIS_URL, 
            decode_responses=True,
            max_connections=10
        )
    
    # Yield a client from the pool
    async with _redis_pool.client() as client:
        yield client

async def get_redis_pubsub():
    """Helper to get a raw connection for PubSub (cannot use pool context)"""
    return aioredis.from_url(config.REDIS_URL, decode_responses=True)