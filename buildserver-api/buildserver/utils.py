"""
Various helper functions for use across modules
"""

from pathlib import Path
import logging
import subprocess
import os
import shutil

from buildserver.config import LOG_LEVEL

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def get_dir_name(url: str):
    """
    Determine directory name based on the supplied repository url
    """
    # path can start with git@*.*:, http://*.com/, or be a local directory
    # check if 'url' is a local directory first
    url_to_path = Path(url)
    if Path.is_dir(url_to_path):
        return url_to_path.name
    if url.startswith("git"):
        repo = url.split("/")[-1:]  # split on the user/repo_name.git
    else:
        repo = url.split("com/")[-1:]
        repo = url.split("/")[-1:]
    repo = repo[0].split(".")[0]  # remove the .git
    return repo


def get_commit_hash(path: Path, logger: logging.Logger) -> str:
    """
    Get commit hash of the checked out branch
    """
    try:
        os.chdir(path)
        logger.debug("Path: %s cwd: %s", path, Path.cwd())
    except OSError as e:
        logger.error("chdir: %s", e)
        raise e
    p = subprocess.run(
        ["/usr/bin/git", "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE
    )  # NOTE: consider using command pattern for all of these subproccess calls
    commit_hash = str(p.stdout, encoding="utf-8").strip("\n")
    return commit_hash


def get_remote_hash(remote_url: str) -> str:
    proc = subprocess.run(
        ["/usr/bin/git", "ls-remote", remote_url, "HEAD"],
        stdout=subprocess.PIPE,
        check=True,
    )
    # git ls-remote output: ba8d19c10bb14810dbb663ae2455e6964cee0e41	HEAD
    remote_hash = str(proc.stdout.split(b"\t")[0], encoding="utf-8")
    logger.debug("Got hash for %s: %s", remote_url, remote_hash)
    return remote_hash


def compare_hashes(local_hash: str, remote_hash: str) -> bool:
    # TODO: handle edge case where None is passed for either hash
    logger.debug("Local: %s Remote: %s", local_hash, remote_hash)
    return local_hash == remote_hash


def cleanup_build_files(build_path: Path):
    """
    Cleanup a build directory after a build has completed
    """
    try:
        shutil.rmtree(build_path)
    except Exception as e:
        logger.error("Failed to remove %s: %s", build_path, e)
