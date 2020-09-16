import asyncio

import aioredis
import uuid
from aioredis.errors import \
    ConnectionClosedError as ServerConnectionClosedError
from fastapi import Depends
from fastapi.routing import APIRouter
from loguru import logger
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from app.core.config import (NUM_PREVIOUS, REDIS_HOST, REDIS_PORT,
                             STREAM_MAX_LEN, XREAD_COUNT, XREAD_TIMEOUT, ALLOWED_ROOMS)
import contextvars

router = APIRouter()


cvar_client_addr = contextvars.ContextVar('client_addr', default=None)
cvar_chat_info = contextvars.ContextVar('chat_info', default=None)
cvar_tenant = contextvars.ContextVar('tenant', default=None)
cvar_redis = contextvars.ContextVar('redis', default=None)


async def verify_user_for_room(chat_info):
    verified = True
    pool = await get_redis_pool()
    if not pool:
        logger.info('Redis connection failure')
        return False
    # check for duplicated user names
    already_exists = await pool.sismember(cvar_tenant.get()+":users", cvar_chat_info.get()['username'])
    if already_exists:
        logger.error(chat_info['username'] +' user already_exists in ' + chat_info['room'])
        verified = False
    # check for restricted names

    # check for restricted rooms
    # check for non existent rooms
    # whitelist rooms
    if not chat_info['room'] in ALLOWED_ROOMS:
        verified = False
    pool.close()
    return verified


async def get_redis_pool():
    try:
        pool = await aioredis.create_redis_pool(
            (REDIS_HOST, REDIS_PORT), encoding='utf-8')
        return pool
    except ConnectionRefusedError as e:
        logger.info('cannot connect to redis on:', REDIS_HOST, REDIS_PORT)
        return None


async def get_chat_history():
    pass


async def ws_send_moderator(websocket: WebSocket, chat_info: dict):
    """
    wait for new items on chat stream and
    send data from server to client over a WebSocket

    :param websocket:
    :type websocket:
    :param chat_info:
    :type chat_info:
    """
    pool = await get_redis_pool()
    streams = chat_info['room'].split(',')
    latest_ids = ['$' for i in streams]
    ws_connected = True
    logger.info(streams, latest_ids)
    while pool and ws_connected:
        try:
            events = await pool.xread(
                streams=streams,
                count=XREAD_COUNT,
                timeout=XREAD_TIMEOUT,
                latest_ids=latest_ids
            )
            for _, e_id, e in events:
                e['e_id'] = e_id
                await websocket.send_json(e)
                #latest_ids = [e_id]
        except ConnectionClosedError:
            ws_connected = False

        except ConnectionClosedOK:
            ws_connected = False


async def ws_send(websocket: WebSocket, chat_info: dict):
    """
    wait for new items on chat stream and
    send data from server to client over a WebSocket

    :param websocket:
    :type websocket:
    :param chat_info:
    :type chat_info:
    """
    pool = await get_redis_pool()
    latest_ids = ['$']
    ws_connected = True
    first_run = True
    while pool and ws_connected:
        try:
            if first_run:
                # fetch some previous chat history
                events = await pool.xrevrange(
                    stream=cvar_tenant.get() + ":stream",
                    count=NUM_PREVIOUS,
                    start='+',
                    stop='-'
                )
                first_run = False
                events.reverse()
                for e_id, e in events:
                    e['e_id'] = e_id
                    await websocket.send_json(e)
            else:
                events = await pool.xread(
                    streams=[cvar_tenant.get() + ":stream"],
                    count=XREAD_COUNT,
                    timeout=XREAD_TIMEOUT,
                    latest_ids=latest_ids
                )
                for _, e_id, e in events:
                    e['e_id'] = e_id
                    await websocket.send_json(e)
                    latest_ids = [e_id]
            #logger.info('################contextvar ', cvar_tenant.get())
        except ConnectionClosedError:
            ws_connected = False

        except ConnectionClosedOK:
            ws_connected = False

        except ServerConnectionClosedError:
            logger.info('redis server connection closed')
            return
    pool.close()


async def ws_recieve(websocket: WebSocket, chat_info: dict):
    """
    receive json data from client over a WebSocket, add messages onto the
    associated chat stream

    :param websocket:
    :type websocket:
    :param chat_info:
    :type chat_info:
    """

    ws_connected = False
    pool = await get_redis_pool()
    added = await add_room_user(chat_info, pool)

    if added:
        await announce(pool, chat_info, 'connected')
        ws_connected = True
    else:
        logger.info('duplicate user error')

    while ws_connected:
        try:
            data = await websocket.receive_json()
            #logger.info(data)
            if type(data) == list and len(data):
                data = data[0]
            fields = {
                'uname': chat_info['username'],
                'msg': data['msg'],
                'type': 'comment',
                'room': chat_info['room']
            }
            logger.info(cvar_tenant.get())
            await pool.xadd(stream=cvar_tenant.get() + ":stream",
                            fields=fields,
                            message_id=b'*',
                            max_len=STREAM_MAX_LEN)
            #logger.info('################contextvar ', cvar_tenant.get())
        except WebSocketDisconnect:
            await remove_room_user(chat_info, pool)
            await announce(pool, chat_info, 'disconnected')
            ws_connected = False

        except ServerConnectionClosedError:
            logger.info('redis server connection closed')
            return

        except ConnectionRefusedError:
            logger.info('redis server connection closed')
            return

    pool.close()


async def add_room_user(chat_info: dict, pool):
    #added = await pool.sadd(chat_info['room']+":users", chat_info['username'])
    added = await pool.sadd(cvar_tenant.get()+":users", cvar_chat_info.get()['username'])
    return added


async def remove_room_user(chat_info: dict, pool):
    #removed = await pool.srem(chat_info['room']+":users", chat_info['username'])
    removed = await pool.srem(cvar_tenant.get()+":users", cvar_chat_info.get()['username'])
    return removed


async def room_users(chat_info: dict, pool):
    #users = await pool.smembers(chat_info['room']+":users")
    users = await pool.smembers(cvar_tenant.get()+":users")
    logger.info(len(users))
    return users


async def announce(pool, chat_info: dict, action: str):
    """
    add an announcement event onto the redis chat stream
    """
    users = await room_users(chat_info, pool)
    fields = {
        'msg': f"{chat_info['username']} {action}",
        'action': action,
        'type': 'announcement',
        'users': ", ".join(users),
        'room': chat_info['room']
    }
    #logger.info(fields)

    await pool.xadd(stream=cvar_tenant.get() + ":stream",
                    fields=fields,
                    message_id=b'*',
                    max_len=STREAM_MAX_LEN)


async def chat_info_vars(username: str = None, room: str = None):
    """
    URL parameter info needed for a user to participate in a chat
    :param username:
    :type username:
    :param room:
    :type room:
    """
    if username is None and room is None:
        return {"username": str(uuid.uuid4()), "room": 'chat:1'}
    return {"username": username, "room": room}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket,
                             chat_info: dict = Depends(chat_info_vars)):
    #logger.info('request.hostname', websocket.url.hostname)
    tenant_id = ":".join([websocket.url.hostname.replace('.', '_'),
                          chat_info['room']])
    cvar_tenant.set(tenant_id)
    cvar_chat_info.set(chat_info)


    # check the user is allowed into the chat room
    verified = await verify_user_for_room(chat_info)
    # open connection
    await websocket.accept()
    if not verified:

        logger.info('failed verification')
        logger.info(chat_info)
        await websocket.close()
    else:

        # spin up coro's for inbound and outbound communication over the socket
        await asyncio.gather(ws_recieve(websocket, chat_info),
                             ws_send(websocket, chat_info))
