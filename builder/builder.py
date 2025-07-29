import os
import subprocess
import logging
from pathlib import Path

logging.basicConfig()
logger = logging.getLogger(f"builder.{__name__}")  # log format will be [MODULE: MSG]
logger.setLevel(logging.INFO)


class Builder:
    BUILD_CMD = "make"
    BUILD_DIR = Path("../build").resolve()

    def __init__(self):
        pass

    def clone_repo(self, repo):
        """
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

        Creates a subprocess
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
            repo:
        raises:
            OSError
            CalledProcessError
        """
        try:
            self.clone_repo(repo)
        except Exception as e:
            logger.error("Failed to clone repo: %s", e)
            raise e
        try:
            self.build(repo)
        except Exception as e:
            logger.error("Failed to build program: %s", e)
            raise e
