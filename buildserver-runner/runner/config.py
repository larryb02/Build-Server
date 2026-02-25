import logging

from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

LOG_LEVEL = config("LOG_LEVEL", default=logging.INFO)
RABBITMQ_HOST = config("RABBITMQ_HOST", default="rabbitmq")
RABBITMQ_USER = config("RABBITMQ_USER", default="guest")
RABBITMQ_PASS = config("RABBITMQ_PASS", default="guest", cast=Secret)
RABBITMQ_PORT = config("RABBITMQ_PORT", default=5672)
APISERVER_HOST = config("APISERVER_HOST", default="http://localhost:8000")
