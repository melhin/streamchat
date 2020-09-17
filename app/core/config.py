import logging
import sys
from typing import List, Optional

from loguru import logger
from pyparsing import Optional
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

from app.core.logging import InterceptHandler

API_PREFIX = "/api"

JWT_TOKEN_PREFIX = "Token"  # noqa: S105
VERSION = "0.0.0"

config = Config(".env")

DEBUG: bool = config("DEBUG", cast=bool, default=False)

#DATABASE_URL: DatabaseURL = config("DB_CONNECTION", cast=DatabaseURL)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)

SECRET_KEY: Secret = config("SECRET_KEY", cast=Secret, default="somesecret")

PROJECT_NAME: str = config("PROJECT_NAME", default="StreamChat")
ALLOWED_HOSTS: List[str] = config(
    "ALLOWED_HOSTS",
    cast=CommaSeparatedStrings,
    default="",
)

# logging configuration

LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGGERS = ("uvicorn.asgi", "uvicorn.access")

logging.getLogger().handlers = [InterceptHandler()]
for logger_name in LOGGERS:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler(level=LOGGING_LEVEL)]

logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])

REDIS_DSN: str = config("REDIS_DSN", cast=str, default='redis://localhost:6379/1')
REDIS_PASSWORD: str = config("REDIS_PASSWORD", cast=str, default=None)

TEMPLATES = 'templates'


PORT = 9080
HOST = "0.0.0.0"

XREAD_TIMEOUT = 0
XREAD_COUNT = 100
NUM_PREVIOUS = 30
STREAM_MAX_LEN = 1000
ALLOWED_ROOMS = ['chat1', 'chat2', 'chat3']
