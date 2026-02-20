"""Redis 연결 관리."""

import redis
from redis import asyncio as aioredis

from app.core.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
async_redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


def get_redis():
    """FastAPI dependency — Redis 클라이언트 제공."""
    return redis_client


def get_async_redis():
    """FastAPI dependency — Async Redis 클라이언트 제공."""
    return async_redis_client
