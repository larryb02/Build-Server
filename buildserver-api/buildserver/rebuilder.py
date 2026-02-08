"""
Rebuilder periodically checks for new commits on a repository
and triggers new build jobs based on the state of the repository

TODO: Polling is a stopgap. Ideally this gets replaced by webhooks
triggered from VCS platforms (GitHub, GitLab, etc.) on push events.
Need to research how each platform handles webhook configuration.
"""

import logging
import subprocess
import time

import requests

from buildserver.config import Config
from buildserver.utils import compare_hashes, get_remote_hash

config = Config()

API_ENDPOINT = "http://localhost:8000"
SLEEP_FOR = config.SLEEP_FOR

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


def check_for_rebuild(job: dict):
    """Check if a job's repo has new commits and register a rebuild if so."""
    repo_url = job["git_repository_url"]
    local_hash = job.get("commit_hash")
    if local_hash is None:
        return

    try:
        remote_hash = get_remote_hash(repo_url)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to get remote hash for %s: %s", repo_url, e)
        return

    if not compare_hashes(local_hash, remote_hash):
        logger.info("%s has new commits. Rebuilding", repo_url)
        try:
            requests.post(
                f"{API_ENDPOINT}/jobs/register",
                json={"git_repository_url": repo_url},
                timeout=5,
            )
        except requests.RequestException as e:
            logger.error("Failed to register rebuild for %s: %s", repo_url, e)


def run():
    """Poll for new commits and register rebuild jobs."""
    logger.info("Started rebuilder")
    while True:
        time.sleep(SLEEP_FOR)
        logger.debug("Checking for new commits")
        try:
            resp = requests.get(
                f"{API_ENDPOINT}/jobs", params={"latest": True}, timeout=5
            )
            resp.raise_for_status()
            jobs = resp.json()
            logger.debug("Got jobs: %s", jobs)
            for job in jobs:
                check_for_rebuild(job)
        except requests.RequestException as e:
            logger.error("Failed to fetch jobs: %s", e)
            continue
