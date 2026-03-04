import logging

from dynaconf import Dynaconf

settings = Dynaconf(envvar_prefix="BS")

LOG_LEVEL = settings.get("LOG_LEVEL", logging.INFO)
RABBITMQ_HOST = settings.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = settings.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = settings.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_PORT = settings.get("RABBITMQ_PORT", 5672)
APISERVER_HOST = settings.get("APISERVER_HOST", "http://localhost:8000")
