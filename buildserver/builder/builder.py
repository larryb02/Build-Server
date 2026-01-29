"""
Functions for compiling C programs
"""

import os
import enum
import shutil
import subprocess
import logging
from pathlib import Path


import buildserver.config as config
import buildserver.utils as utils

logging.basicConfig()
logger = logging.getLogger(f"{__name__}")  # log format will be [MODULE: MSG]
logger.setLevel(config.LOG_LEVEL)  # grab from config


class BuildStatus(enum.Enum):
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"


BUILD_CMD = "make"
BUILD_DIR = Path(config.BUILD_DIR).resolve()


def clone_repo(repo: str):
    """
    Clone git repository into build directory
    params:
        repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
    raises:
        OSError
        CalledProcessError
    """
    logger.info(f"Cloning {repo} into {BUILD_DIR}")
    try:
        os.chdir(BUILD_DIR)
    except OSError as e:
        logger.error(f"Failed to change directory: {e.strerror}")
        raise e
    subprocess.run(["/usr/bin/git", "clone", repo], check=True)
    try:
        repo = utils.get_dir_name(repo)
        commit_hash = utils.get_commit_hash(Path(BUILD_DIR, repo), logger)
    except Exception as e:
        logger.error(f"Failed to get commit hash: {e}")
    logger.info(f"Cloned {repo} at {commit_hash} PWD: {Path.cwd()}")
    return commit_hash


def build(repo: str):
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
        os.chdir(Path(BUILD_DIR, repo))
    except OSError as e:
        logger.error(f"Failed to change directory: {e.strerror}")
        raise e
    subprocess.run(BUILD_CMD, check=True)


def run(repo: str):
    """
    Clone and build C program
    params:
        repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
    raises:
        OSError
        CalledProcessError
    """
    try:
        commit_hash = clone_repo(repo)
    except Exception as e:
        raise e
    try:
        build_path = utils.get_dir_name(repo)
        build(build_path)
        status = BuildStatus.SUCCEEDED
    except Exception as e:
        logger.error("Failed to build program: %s", e)
        status = BuildStatus.FAILED
        utils.cleanup_build_files(Path(BUILD_DIR, build_path))
    return {
        "git_repository_url": repo,
        "commit_hash": commit_hash,
        "build_status": status,
    }
