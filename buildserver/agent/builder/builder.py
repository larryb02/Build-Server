"""
Functions for compiling C programs
"""

import logging
import subprocess
import tempfile
from pathlib import Path

from buildserver import utils
from buildserver.config import Config

config = Config()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)

BUILD_CMD = "make"


class BuildError(Exception):
    """Raised when a build fails."""

    pass


class CloneError(Exception):
    """Raised when cloning a repository fails."""

    pass


def clone_repo(repo: str, build_dir: Path) -> str:
    """
    Clone git repository into build directory.

    Args:
        repo: Git repository URL (git@ or https://)
        build_dir: Directory to clone into

    Returns:
        The commit hash of the cloned repo.

    Raises:
        CloneError: If cloning fails.
    """
    logger.info("Cloning %s into %s", repo, build_dir)
    try:
        result = subprocess.run(
            ["/usr/bin/git", "clone", repo],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise CloneError(f"Failed to clone {repo}: {e.stderr}") from e

    repo_name = utils.get_dir_name(repo)
    repo_path = build_dir / repo_name

    try:
        commit_hash = utils.get_commit_hash(repo_path, logger)
    except Exception as e:
        raise CloneError(f"Failed to get commit hash: {e}") from e

    logger.info("Cloned %s at %s", repo_name, commit_hash)
    return commit_hash


def build(repo_path: Path) -> None:
    """
    Compile C program into a binary.

    Args:
        repo_path: Path to the cloned repository.

    Raises:
        BuildError: If compilation fails.
    """
    logger.info("Building %s", repo_path)
    try:
        subprocess.run(
            BUILD_CMD,
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
            shell=True,
        )
    except subprocess.CalledProcessError as e:
        raise BuildError(f"Build failed: {e.stderr}") from e


def run(repo: str) -> None:
    """
    Clone and build a C program in an isolated temp directory.

    Args:
        repo: Git repository URL.

    Raises:
        CloneError: If cloning fails.
        BuildError: If compilation fails.
    """
    build_dir = Path(tempfile.mkdtemp(prefix="job_"))
    logger.info("Created temp build directory: %s", build_dir)

    try:
        clone_repo(repo, build_dir)
        repo_name = utils.get_dir_name(repo)
        repo_path = build_dir / repo_name
        build(repo_path)
    except (CloneError, BuildError):
        utils.cleanup_build_files(build_dir)
        raise
