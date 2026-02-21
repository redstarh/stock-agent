"""Redis 연결 관리."""

import logging
import ssl as ssl_module

import redis
from redis import asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_redis_kwargs() -> dict:
    """Build Redis connection kwargs with optional auth and SSL."""
    kwargs = {"decode_responses": True}

    if settings.redis_ssl:
        ssl_context = ssl_module.create_default_context()
        if settings.redis_ssl_ca:
            ssl_context.load_verify_locations(settings.redis_ssl_ca)
        kwargs["ssl"] = True
        kwargs["ssl_ca_certs"] = settings.redis_ssl_ca or None

    return kwargs


_redis_kwargs = _build_redis_kwargs()

# Build Redis URL with password if configured
_redis_url = settings.redis_url

redis_client = redis.Redis.from_url(_redis_url, **_redis_kwargs)
async_redis_client = aioredis.from_url(_redis_url, **_redis_kwargs)


def get_redis():
    """FastAPI dependency — Redis 클라이언트 제공."""
    return redis_client


def get_async_redis():
    """FastAPI dependency — Async Redis 클라이언트 제공."""
    return async_redis_client
