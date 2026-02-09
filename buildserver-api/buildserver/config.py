"""Configuration values loaded from environment variables"""

import logging

from starlette.config import Config as StarletteConfig
from starlette.datastructures import Secret

config = StarletteConfig(".env")

LOG_LEVEL = config("LOG_LEVEL", default=logging.INFO)

DATABASE_PORT = config("DATABASE_PORT", default=5432, cast=int)
DATABASE_USER = config("DATABASE_USER", default="postgres")
DATABASE_PASSWORD = config("DATABASE_PASSWORD", default="example", cast=Secret)
DATABASE_HOSTNAME = config("DATABASE_HOSTNAME", default="localhost")
DATABASE_NAME = config("DATABASE_NAME", default="postgres")
DATABASE_URI = (
    f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"
)

SLEEP_FOR = config("SLEEP_FOR", default=60 * 15, cast=int)
TIMEOUT = config("TIMEOUT", default=60, cast=int)

RABBITMQ_HOST = config("RABBITMQ_HOST", default="rabbitmq")
RABBITMQ_PORT = config("RABBITMQ_PORT", default=5672, cast=int)
RABBITMQ_USER = config("RABBITMQ_USER", default="guest")
RABBITMQ_PASSWORD = config("RABBITMQ_PASSWORD", default="guest", cast=Secret)

ARTIFACT_REPOSITORY_ROOT = config("ARTIFACT_REPOSITORY_ROOT", default="")
