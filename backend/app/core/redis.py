from collections.abc import Awaitable

from redis.asyncio import Redis

from app.core.config import settings


async def ping_redis() -> None:
    """Confirm Redis accepts a command. HITL state will use this client later."""
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
