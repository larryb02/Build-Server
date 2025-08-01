import os
import enum
import subprocess
import logging
from pathlib import Path
import re

from api.config import LOG_LEVEL




class Builder:
    BUILD_CMD = "make"
    BUILD_DIR = Path("../build").resolve()

    BUILD_STATUS = enum.Enum("STATUS", ["FAILED", "SUCCEEDED"])

    def __init__(self):
        logging.basicConfig()
        self.logger = logging.getLogger(f"{__name__}")  # log format will be [MODULE: MSG]
        self.logger.setLevel(LOG_LEVEL) # grab from config

    def clone_repo(self, repo):
        """
        Clone git repository into build directory

        params:
            repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
        raises:
            OSError
            CalledProcessError
        """
        logger.info("Cloning %s into %s", repo, Builder.BUILD_DIR)
        try:
            os.chdir(Builder.BUILD_DIR)
        except OSError as e:
            logger.error("Failed to change directory: %s", e.strerror)
            raise e
        subprocess.run(["/usr/bin/git", "clone", repo], check=True)

    def build(self, repo):
        """
        Compile C program into a binary

        params:
            repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
        raises:
            OSError
            CalledProcessError
        """
        logger.info("Building %s")
        try:
            os.chdir(Path(Builder.BUILD_DIR, repo.name))
        except OSError as e:
            logger.error("Failed to change directory: %s", e.strerror)
            raise e
        subprocess.run(Builder.BUILD_CMD, check=True)

    def run(self, repo):
        """
        Clone and build C program

        params:
            repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
        raises:
            OSError
            CalledProcessError
        """
        try:
            repo = Path(repo)
            self.clone_repo(repo)
            self.build(repo)
        except Exception as e:
            logger.error("Failed to build program: %s", e)
            return Builder.BUILD_STATUS.FAILED
        return Builder.BUILD_STATUS.SUCCEEDED
