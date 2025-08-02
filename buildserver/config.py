import platform
from starlette.config import Config
from starlette.datastructures import Secret
import logging

config = Config(".env")

DATABASE_PORT = config("DATABASE_PORT")
DATABASE_USER = config("DATABASE_USER")
DATABASE_PASSWORD = config("DATABASE_PASSWORD", cast=Secret)
DATABASE_HOSTNAME = config("DATABASE_HOSTNAME")
DATABASE_NAME = config("DATABASE_NAME")
DATABASE_URI = f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:{DATABASE_PORT}/{DATABASE_NAME}"

LOG_LEVEL = config("LOG_LEVEL", default=logging.INFO)

BUILD_DIR = (
    config("WINDOWS_BUILD_DIRECTORY")
    if platform.system() == "WINDOWS"
    else config("POSIX_BUILD_DIRECTORY")
)

SLEEP_FOR = config("SLEEP_FOR", default=60 * 15, cast=int)
TIMEOUT = config("TIMEOUT", default=60, cast=int)

ARTIFACT_REPOSITORY_ROOT = config("ARTIFACT_REPOSITORY_ROOT")
