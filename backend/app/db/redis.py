"""
Redis async client — used for refresh token storage.

Key schema:
  rt:{user_id}:{jti}  →  "valid"   TTL = REFRESH_TOKEN_EXPIRE_DAYS * 86400

Set the env var  DEV_FAKE_REDIS=1  to use fakeredis (no real Redis needed).
"""
import os

import redis.asyncio as aioredis
from app.core.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        if os.getenv("DEV_FAKE_REDIS") == "1":
            import fakeredis.aioredis as fake_aioredis  # type: ignore[import]
            _redis_client = fake_aioredis.FakeRedis(decode_responses=True)
        else:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
    return _redis_client


def refresh_token_key(user_id: str, jti: str) -> str:
    return f"rt:{user_id}:{jti}"
