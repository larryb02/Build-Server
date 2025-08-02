import logging
import asyncio
import subprocess

from buildserver.builder.agent import Agent
from buildserver.builds.service import get_all_unique_builds, register
import buildserver.config as config


"""
Background task that periodically checks for new commits and schedules rebuilds

Runs for the entire lifetime of the application
"""

SLEEP_FOR = config.SLEEP_FOR
ASYNC_TIMEOUT = config.TIMEOUT

logging.basicConfig()
logger = logging.getLogger(f"{__name__}")
logger.setLevel(config.LOG_LEVEL)


class Rebuilder:

    def __init__(self, agent: Agent):
        self.agent = agent

    async def run(self):
        try:
            logger.info(f"Started rebuilder [{id(asyncio.get_running_loop())}]")
            while True:
                await asyncio.sleep(SLEEP_FOR)
                logger.debug(f"Checking for new commits")
                try:
                    async with asyncio.timeout(ASYNC_TIMEOUT):
                        builds = get_all_unique_builds()
                        logger.debug(f"Got builds: {builds}")
                        for build in builds:
                            remote_url = build.git_repository_url
                            remote_hash = get_remote_hash(remote_url)
                            if not compare_hashes(
                                local_hash=build.commit_hash, remote_hash=remote_hash
                            ):
                                logger.info(f"{remote_url} got new commits. Rebuilding")
                                await register(remote_url, self.agent)
                except TimeoutError as e:
                    logger.error(f"Rebuilder timed out: {e}")
                    raise e
        except Exception as e:
            logger.error(f"Unknown error occurred: {e}")
            raise e


def compare_hashes(local_hash: str, remote_hash: str):
    logger.debug(f"Local: {local_hash} Remote: {remote_hash}")
    return local_hash == remote_hash


def get_remote_hash(remote_url: str) -> str:
    # NOTE: going to create a command pattern that works like this ->
    proc = subprocess.run(
        ["/usr/bin/git", "ls-remote", remote_url, "HEAD"], stdout=subprocess.PIPE, check=True
    )
    # git ls-remote output: ba8d19c10bb14810dbb663ae2455e6964cee0e41	HEAD,
    # so we only take before the tab character
    remote_hash = str(proc.stdout.split(b"\t")[0], encoding="utf-8")
    logger.debug(f"Got hash for {remote_url}: {remote_hash}")
    return remote_hash
