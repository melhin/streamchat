import os
import socket

from fastapi import Request
from fastapi.routing import APIRouter
from starlette.templating import Jinja2Templates

from app.core.config import PORT, TEMPLATES

router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATES)


def get_local_ip():
    """
    copy and paste from
    https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    """
    if os.environ.get('CHAT_HOST_IP', False):
        return os.environ['CHAT_HOST_IP']
    try:
        ip = [l for l in (
            [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if
             not ip.startswith("127.")][:1], [
                [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s
                 in
                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][
            0][
            0]
    except OSError as e:
        logger.info(e)
        return '127.0.0.1'

    return ip


@router.get("/")
async def get(request: Request):
    return templates.TemplateResponse("chat.html",
                                      {"request": request,
                                       "ip": get_local_ip(),
                                       "port": PORT})
