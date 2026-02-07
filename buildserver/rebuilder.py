"""
Rebuilder periodically checks for new commits on a repository
and triggers new build jobs based on the state of the repository
"""

import logging
import subprocess

# from buildserver.agent.agent import Agent, JobType
# from buildserver.services.builds import get_all_unique_builds, register
from buildserver.config import Config

config = Config()
# from buildserver.api.builds.models import BuildCreate

SLEEP_FOR = config.SLEEP_FOR

logging.basicConfig()
logger = logging.getLogger(f"{__name__}")
logger.setLevel(config.LOG_LEVEL)


# class Rebuilder:

#     def __init__(self):

# async def run(self):
#     try:
#         logger.info("Started rebuilder [%d]", id(asyncio.get_running_loop()))
#         while True:
#             await asyncio.sleep(SLEEP_FOR)
#             logger.debug("Checking for new commits")
#             builds = get_all_unique_builds()
#             logger.debug("Got builds: %s", str(builds))
#             for build in builds:
#                 remote_url = build.git_repository_url
#                 remote_hash = get_remote_hash(remote_url)
#                 if not compare_hashes(
#                     local_hash=build.commit_hash, remote_hash=remote_hash
#                 ):
#                     logger.info("%s got new commits. Rebuilding", remote_url)
#                     await register(BuildCreate(git_repository_url=remote_url))
#                     await self.agent.add_job(
#                         JobType.BUILD_PROGRAM, (remote_url, build.build_id)
#                     )
#     except Exception as e:
#         logger.error("Unknown error occurred: %s", e)
#         raise e


def compare_hashes(local_hash: str, remote_hash: str):
    logger.debug("Local: %s Remote: %s", local_hash, remote_hash)
    return local_hash == remote_hash


def get_remote_hash(remote_url: str) -> str:
    # NOTE: going to create a command pattern that works like this ->
    proc = subprocess.run(
        ["/usr/bin/git", "ls-remote", remote_url, "HEAD"],
        stdout=subprocess.PIPE,
        check=True,
    )
    # git ls-remote output: ba8d19c10bb14810dbb663ae2455e6964cee0e41	HEAD,
    # so we only take before the tab character
    remote_hash = str(proc.stdout.split(b"\t")[0], encoding="utf-8")
    logger.debug("Got hash for %s: %s", remote_url, remote_hash)
    return remote_hash
