"""Configuration values loaded from environment variables"""

import logging
import platform

from starlette.config import Config as StarletteConfig
from starlette.datastructures import Secret


class Config:
    """Lazy-loading configuration that reads values on first access"""

    def __init__(self):
        self._config = StarletteConfig(".env")
        self._database_uri = None
        self._build_dir = None

    @property
    def DATABASE_PORT(self):
        return self._config("DATABASE_PORT")

    @property
    def DATABASE_USER(self):
        return self._config("DATABASE_USER")

    @property
    def DATABASE_PASSWORD(self):
        return self._config("DATABASE_PASSWORD", cast=Secret)

    @property
    def DATABASE_HOSTNAME(self):
        return self._config("DATABASE_HOSTNAME")

    @property
    def DATABASE_NAME(self):
        return self._config("DATABASE_NAME")

    @property
    def DATABASE_URI(self):
        if self._database_uri is None:
            self._database_uri = (
                f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
                f"@{self.DATABASE_HOSTNAME}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            )
        return self._database_uri

    @property
    def LOG_LEVEL(self):
        return self._config("LOG_LEVEL", default=logging.INFO)

    @property
    def BUILD_DIR(self):
        if self._build_dir is None:
            self._build_dir = (
                self._config("WINDOWS_BUILD_DIRECTORY")
                if platform.system() == "WINDOWS"
                else self._config("POSIX_BUILD_DIRECTORY")
            )
        return self._build_dir

    @property
    def SLEEP_FOR(self):
        return self._config("SLEEP_FOR", default=60 * 15, cast=int)

    @property
    def TIMEOUT(self):
        return self._config("TIMEOUT", default=60, cast=int)

    @property
    def ARTIFACT_REPOSITORY_ROOT(self):
        return self._config("ARTIFACT_REPOSITORY_ROOT")
