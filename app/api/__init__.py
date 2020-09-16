from fastapi.routing import APIRouter
from app.api import index, streamsocket

router = APIRouter()
router.include_router(index.router, prefix='/base')
router.include_router(streamsocket.router, prefix='/stream')

