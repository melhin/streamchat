
from aioredis.errors import \
    ConnectionClosedError as ServerConnectionClosedError
from loguru import logger
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from app.core.config import (NUM_PREVIOUS, STREAM_MAX_LEN, XREAD_COUNT,
                             XREAD_TIMEOUT)
from app.db.connection import get_redis_pool
from app.services.user_actions import add_room_user, announce, remove_room_user, record_user_presence, get_user_presence
from sqlalchemy.orm import Session


async def ws_send(websocket: WebSocket, chat_info: dict):
    '''
    wait for new items on chat stream and
    send data from server to client over a WebSocket

    :param websocket:
    :type websocket:
    :param chat_info:
    :type chat_info:
    '''
    redis_connection = await get_redis_pool()
    latest_ids = ['$']
    ws_connected = True
    first_run = True
    while redis_connection and ws_connected:
        try:
            if first_run:
                # fetch some previous chat history
                events = await redis_connection.xrevrange(
                    stream=chat_info['stream'],
                    count=NUM_PREVIOUS,
                    start='+',
                    stop='-'
                )
                first_run = False
                events.reverse()
                last_presence = await get_user_presence(redis_connection, chat_info['username'])
                new_message = False
                for e_id, e in events:
                    e['e_id'] = e_id
                    timestamp = e_id.split('-')[0]
                    if last_presence and e['type'] != 'announcement' and not new_message and \
                            float(timestamp) > float(last_presence):
                        await websocket.send_json({'type': 'new_message'})
                        await record_user_presence(redis_connection, chat_info['username'], timestamp)
                        new_message = True
                    await websocket.send_json(e)
            else:
                events = await redis_connection.xread(
                    streams=[chat_info['stream']],
                    count=XREAD_COUNT,
                    timeout=XREAD_TIMEOUT,
                    latest_ids=latest_ids
                )
                for _, e_id, e in events:
                    e['e_id'] = e_id
                    timestamp = e_id.split('-')[0]
                    await websocket.send_json(e)
                    await record_user_presence(redis_connection, chat_info['username'], timestamp)
                    latest_ids = [e_id]
        except ConnectionClosedError:
            ws_connected = False

        except ConnectionClosedOK:
            ws_connected = False

        except ServerConnectionClosedError:
            logger.info('redis server connection closed')
            return
    redis_connection.close()


async def ws_recieve(websocket: WebSocket, chat_info: dict, db: Session):
    '''
    receive json data from client over a WebSocket, add messages onto the
    associated chat stream

    :param websocket:
    :type websocket:
    :param chat_info:
    :type chat_info:
    '''

    ws_connected = False
    redis_connection = await get_redis_pool()
    added = await add_room_user(chat_info, redis_connection, db)
    if added:
        await announce(redis_connection, chat_info, 'connected')
        ws_connected = True
    else:
        logger.info('duplicate user error')

    while ws_connected:
        try:
            data = await websocket.receive_json()
            if type(data) == list and len(data):
                data = data[0]
            fields = {
                'uname': chat_info['username'],
                'msg': data['msg'],
                'type': 'comment',
                'room': chat_info['room'],
            }
            await redis_connection.xadd(stream=chat_info['stream'],
                            fields=fields,
                            message_id=b'*',
                            max_len=STREAM_MAX_LEN)
        except WebSocketDisconnect:
            await remove_room_user(chat_info, redis_connection, db)
            await announce(redis_connection, chat_info, 'disconnected')
            ws_connected = False

        except ServerConnectionClosedError:
            logger.info('redis server connection closed')
            return

        except ConnectionRefusedError:
            logger.info('redis server connection closed')
            return

    redis_connection.close()
