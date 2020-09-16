import logging

import aioredis

from app.core.config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)


async def get_redis_pool():
    pool = await aioredis.create_redis_pool(
        (REDIS_HOST, REDIS_PORT), encoding='utf-8')
    yield pool
    pool.close()
    await pool.wait_closed()
