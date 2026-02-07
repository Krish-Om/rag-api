import os
from typing import Optional
import redis.asyncio as redis
from app.config import config

redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis Client, create if needed"""
    global redis_client

    if redis_client is None:
        redis_client = await redis.from_url(
            config.redis_url, decode_responses=True  # Auto decode bytes to strings
        )
    return redis_client


async def init_redis():
    await get_redis_client()


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
