import aioredis
from loguru import logger

from app.core.config import STREAM_MAX_LEN


async def add_room_user(chat_info: dict, redis_connection: aioredis.Redis):
    return await redis_connection.sadd(chat_info['users'], chat_info['username'])


async def remove_room_user(chat_info: dict, redis_connection: aioredis.Redis):
    return await redis_connection.srem(chat_info['users'], chat_info['username'])


async def room_users(chat_info: dict, redis_connection: aioredis.Redis):
    users = await redis_connection.smembers(chat_info['users'])
    logger.info(len(users))
    return users


async def record_user_presence(redis_connection: aioredis.Redis, user_name, timestamp):
    await redis_connection.set(user_name, timestamp)


async def get_user_presence(redis_connection: aioredis.Redis, user_name):
    return await redis_connection.get(user_name)


async def announce(redis_connection: aioredis.Redis, chat_info: dict, action: str):
    '''
    add an announcement event onto the redis chat stream
    '''
    users = await room_users(chat_info, redis_connection)
    fields = {
        'msg': f"{chat_info['username']} {action}",
        'action': action,
        'type': 'announcement',
        'users': ', '.join(users),
        'room': chat_info['room'],
    }

    await redis_connection.xadd(stream=chat_info['stream'],
                    fields=fields,
                    message_id=b'*',
                    max_len=STREAM_MAX_LEN)
