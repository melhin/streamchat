from loguru import logger
from app.core.config import STREAM_MAX_LEN


async def add_room_user(chat_info: dict, pool):
    return await pool.sadd(chat_info['users'], chat_info['username'])


async def remove_room_user(chat_info: dict, pool):
    return await pool.srem(chat_info['users'], chat_info['username'])


async def room_users(chat_info: dict, pool):
    users = await pool.smembers(chat_info['users'])
    logger.info(len(users))
    return users


async def record_user_presence(pool, user_name, timestamp):
    await pool.set(user_name, timestamp)


async def get_user_presence(pool, user_name):
    return await pool.get(user_name)


async def announce(pool, chat_info: dict, action: str):
    '''
    add an announcement event onto the redis chat stream
    '''
    users = await room_users(chat_info, pool)
    fields = {
        'msg': f"{chat_info['username']} {action}",
        'action': action,
        'type': 'announcement',
        'users': ', '.join(users),
        'room': chat_info['room'],
    }

    await pool.xadd(stream=chat_info['stream'],
                    fields=fields,
                    message_id=b'*',
                    max_len=STREAM_MAX_LEN)
