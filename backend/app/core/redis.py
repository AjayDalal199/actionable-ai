from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.core.config import settings


def redis_client() -> Redis:
    url = settings.REDIS_URL
    if url is None:
        raise RuntimeError("REDIS_URL is not set")
    return Redis.from_url(
        str(url),
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


@asynccontextmanager
async def open_redis() -> AsyncIterator[Redis]:
    client = redis_client()
    try:
        yield client
    finally:
        await client.aclose()


async def ping_redis() -> None:
    """Confirm Redis accepts a command."""
    url = settings.REDIS_URL
    if url is None:
        raise RuntimeError("REDIS_URL is not set")
    client = Redis.from_url(
        str(url),
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    try:
        pong = client.ping()
        if isinstance(pong, Awaitable):
            await pong
    finally:
        await client.aclose()
