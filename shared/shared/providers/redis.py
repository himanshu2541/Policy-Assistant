from typing import Optional, Dict, Type
from redis import asyncio as aioredis
from shared.config import Config, config as global_config
from shared.interfaces import RedisStrategy

_REDIS_REGISTRY: Dict[str, Type[RedisStrategy]] = {}


def register_redis_strategy(name: str):
    def decorator(cls):
        _REDIS_REGISTRY[name] = cls
        return cls

    return decorator


@register_redis_strategy("standard")
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


@register_redis_strategy("mock")
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
    """
    Manages the lifecycle of the Redis client (Singleton)
    and delegates creation to the registered strategy.
    """

    _instance: Optional[aioredis.Redis] = None

    @classmethod
    def get_client(
        cls, settings: Config = global_config, strategy_type: str = "standard", **kwargs
    ) -> aioredis.Redis:
        """
        Returns a Singleton Redis client.
        If it exists, it returns the existing one (reusing the pool).
        If not, it creates a new one using the specified strategy.
        """
        if cls._instance is not None:
            return cls._instance

        # Look up strategy in registry
        strategy_cls = _REDIS_REGISTRY.get(strategy_type)
        if not strategy_cls:
            raise ValueError(f"Unknown Redis Strategy: {strategy_type}")

        strategy = strategy_cls()
        cls._instance = strategy.create_client(settings, **kwargs)
        return cls._instance  # type: ignore

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
