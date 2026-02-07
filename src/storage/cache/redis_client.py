import json
from typing import Any

import redis.asyncio as redis

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    def __init__(self):
        settings = get_settings()
        self.client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    async def get(self, key: str) -> Any | None:
        value = await self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def incr(self, key: str, ttl: int | None = None) -> int:
        val = await self.client.incr(key)
        if ttl and val == 1:
            await self.client.expire(key, ttl)
        return val

    async def get_rate_limit(self, source: str, window_seconds: int = 60) -> int:
        key = f"rate_limit:{source}"
        count = await self.incr(key, ttl=window_seconds)
        return count

    async def close(self) -> None:
        await self.client.aclose()
