import logging

import aioredis

from app.core.config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)


async def get_redis_pool():
    return await aioredis.create_redis_pool(
        (REDIS_HOST, REDIS_PORT), encoding='utf-8')
