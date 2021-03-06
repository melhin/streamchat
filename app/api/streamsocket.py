import asyncio
import uuid

from fastapi import Depends
from fastapi.routing import APIRouter
from loguru import logger
from starlette.websockets import WebSocket

from app.services.authentication import verify_user_for_room
from app.services.stream_rw import ws_recieve, ws_send
from app.db import get_db
from sqlalchemy.orm import Session

router = APIRouter()


async def chat_info_vars(username: str = None, room: str = None):
    '''
    URL parameter info needed for a user to participate in a chat
    :param username:
    :type username:
    :param room:
    :type room:
    '''
    if username is None and room is None:
        raise
    return {
        'username': username,
        'room': room,
        'users': room + ':users',
        'stream': room + 'stream',
    }


@router.websocket('/ws', name='chatroom_ws')
async def websocket_endpoint(websocket: WebSocket,
                             chat_info: dict = Depends(chat_info_vars),
                             db: Session = Depends(get_db)):
    # check the user is allowed into the chat room
    verified = await verify_user_for_room(chat_info)
    # open connection
    await websocket.accept()
    if not verified:

        logger.error('failed verification')
        await websocket.close()
    else:

        # spin up coroutines for inbound and outbound communication over the socket
        await asyncio.gather(ws_recieve(websocket, chat_info, db),
                             ws_send(websocket, chat_info))
