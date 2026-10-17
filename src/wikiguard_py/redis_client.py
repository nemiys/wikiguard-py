"""Shared async Redis connection — the one place that knows how to connect,
used by both the consumer (rule evaluation, stream stats) and the API
(GET /stats). Mirrors persistence/database.py's single-engine pattern.
"""

from redis.asyncio import Redis

from wikiguard_py.settings import settings

redis_client = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client
