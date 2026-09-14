from redis.asyncio import Redis

from app.core.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    return _client


async def redis_ok() -> bool:
    try:
        return bool(await get_redis().ping())
    except Exception:
        return False


async def acquire_idempotency_lock(key: str, ttl: int = 3600) -> bool:
    return bool(await get_redis().set(f"idem:{key}", "1", nx=True, ex=ttl))
