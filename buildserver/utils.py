"""
Various helper functions for use across modules
"""

from pathlib import Path
import logging
import subprocess
import os
import shutil

from buildserver.config import Config

config = Config()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


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


def cleanup_build_files(build_path: Path):
    """
    Cleanup a build directory after a build has completed
    """
    try:
        shutil.rmtree(build_path)
    except Exception as e:
        logger.error("Failed to remove %s: %s", build_path, e)
