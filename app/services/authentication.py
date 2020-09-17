from app.core.config import ALLOWED_ROOMS
from app.db.connection import get_redis_pool
from loguru import logger


async def verify_user_for_room(chat_info):
    verified = True
    redis_connection =await get_redis_pool()
    if not redis_connection:
        logger.info('Redis connection failure')
        return False
    # check for duplicated user names
    already_exists = await redis_connection.sismember(chat_info['users'], chat_info['username'])
    if already_exists:
        logger.error(chat_info['username'] + ' user already_exists in ' + chat_info['room'])
        verified = False
    # TODO: add more validation here
    # whitelist rooms
    if not chat_info['room'] in ALLOWED_ROOMS:
        verified = False
    redis_connection.close()
    return verified
