import os
import subprocess
import logging

logging.basicConfig()
logger = logging.getLogger(f"builder.{__name__}")  # log format will be [MODULE: MSG]
logger.setLevel(logging.INFO)


class Builder:
    BUILD_CMD = "make"

    def __init__(self):
        pass

    def build(self, build_repo) -> bool:
        """
        Compile C program into a binary

        Creates a subprocess

        returns:
            True -> subprocess returned a status code of zero
            False -> subprocess returned a non-zero status code

        raises:
            OSError
        """
        try:
            os.chdir(build_repo)
        except OSError as e:
            logger.error("Failed to change directory: %s", e.strerror)
            raise e
        proc = subprocess.run(Builder.BUILD_CMD)
        status = proc.returncode
        logger.info("Process exited with status code %d", status)
        return status == 0
