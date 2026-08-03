from __future__ import annotations

import redis.asyncio as redis

from app.core.config import Settings


def create_redis(settings: Settings) -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


class SessionCache:
    """Hot conversation window and memory bundle cache."""

    def __init__(self, client: redis.Redis, *, ttl_seconds: int = 60 * 60) -> None:
        self._client = client
        self._ttl = ttl_seconds

    def _turns_key(self, user_id: str, room_name: str) -> str:
        return f"session:{user_id}:{room_name}:turns"

    def _bundle_key(self, user_id: str) -> str:
        return f"memory_bundle:{user_id}"

    def _rate_key(self, user_id: str, tool_name: str) -> str:
        return f"tool_rate:{user_id}:{tool_name}"

    async def append_turn(self, user_id: str, room_name: str, role: str, content: str) -> None:
        key = self._turns_key(user_id, room_name)
        await self._client.rpush(key, f"{role}:{content}")
        await self._client.ltrim(key, -40, -1)
        await self._client.expire(key, self._ttl)

    async def get_turns(self, user_id: str, room_name: str) -> list[str]:
        return await self._client.lrange(self._turns_key(user_id, room_name), 0, -1)

    async def set_memory_bundle(self, user_id: str, bundle_json: str) -> None:
        await self._client.set(self._bundle_key(user_id), bundle_json, ex=self._ttl)

    async def get_memory_bundle(self, user_id: str) -> str | None:
        return await self._client.get(self._bundle_key(user_id))

    async def check_rate_limit(
        self,
        user_id: str,
        tool_name: str,
        *,
        limit: int = 30,
        window_seconds: int = 60,
    ) -> bool:
        key = self._rate_key(user_id, tool_name)
        count = await self._client.incr(key)
        if count == 1:
            await self._client.expire(key, window_seconds)
        return count <= limit
