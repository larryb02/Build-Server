"""Configuration values loaded from environment variables"""

import logging

from dynaconf import Dynaconf

settings = Dynaconf(envvar_prefix="BS")

LOG_LEVEL = settings.get("LOG_LEVEL", logging.INFO)

DATABASE_PORT = settings.get("DATABASE_PORT", 5432)
DATABASE_USER = settings.get("DATABASE_USER", "postgres")
DATABASE_PASSWORD = settings.get("DATABASE_PASSWORD", "example")
DATABASE_HOSTNAME = settings.get("DATABASE_HOSTNAME", "localhost")
DATABASE_NAME = settings.get("DATABASE_NAME", "postgres")
DATABASE_URI = (
    f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"
)

SLEEP_FOR = settings.get("SLEEP_FOR", 60 * 15)
TIMEOUT = settings.get("TIMEOUT", 60)

ARTIFACT_REPOSITORY_ROOT = settings.get("ARTIFACT_REPOSITORY_ROOT", "")
