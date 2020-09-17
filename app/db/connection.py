import logging

import aioredis

from app.core.config import REDIS_DSN

logger = logging.getLogger(__name__)


async def get_redis_pool():
    return await aioredis.create_redis(REDIS_DSN, encoding='utf-8')
