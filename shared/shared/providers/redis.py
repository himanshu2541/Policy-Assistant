from typing import Optional
from redis import asyncio as aioredis
from shared.config import Config, config as global_config
from shared.interfaces import RedisStrategy

class StandardRedisStrategy(RedisStrategy):
    def create_client(self, settings: Config, **kwargs) -> aioredis.Redis:
        default_kwargs = {
            "decode_responses": True,
            "encoding": "utf-8",
            "max_connections": 10,
            "socket_timeout": 5,
        }
        connection_args = {**default_kwargs, **kwargs}
        return aioredis.from_url(settings.REDIS_URL, **connection_args)

class MockRedisStrategy(RedisStrategy):
    """
    Requires 'fakeredis' to be installed.
    """
    def create_client(self, settings: Config, **kwargs):
        try:
            from fakeredis import aioredis as fake_aioredis
            return fake_aioredis.FakeRedis(decode_responses=True)
        except ImportError:
            raise ImportError("Install 'fakeredis' to use MockRedisStrategy")

class RedisFactory:
    _strategies = {
        "standard": StandardRedisStrategy(),
        "mock": MockRedisStrategy()
    }
    _instance: Optional[aioredis.Redis] = None

    @classmethod
    def get_client(cls, settings: Config = global_config, strategy_type: str = "standard", **kwargs) -> aioredis.Redis:
        """
        Returns a Singleton Redis client.
        If it exists, it returns the existing one (reusing the pool).
        If not, it creates a new one.
        """
        if cls._instance is not None:
            return cls._instance
        
        strategy = cls._strategies.get(strategy_type)
        if not strategy:
            raise ValueError(f"Unknown Redis Strategy: {strategy_type}")
        cls._instance = strategy.create_client(settings, **kwargs)
        return cls._instance # type: ignore

    @classmethod
    def reset(cls):
        """Resets the Redis client instance (for testing purposes)."""
        cls._instance = None
    
    @classmethod
    async def close(cls):
        """Closes the Redis client connection (if exists)."""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None