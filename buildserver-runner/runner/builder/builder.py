"""
Functions for compiling C programs
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path

from runner import utils
from runner.config import LOG_LEVEL
from runner.types import Job

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

BUILD_CMD = "make"


def _run_script(script: str, cwd: Path = None):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write("#!/bin/bash\n" + script)
        script_path = Path(f.name)

    os.chmod(script_path, 0o755)

    with subprocess.Popen(
        [str(script_path)],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as proc:
        for line in proc.stdout:
            logger.info(line.rstrip())
    if proc.returncode != 0:
        raise BuildError(f"Script exited with code {proc.returncode}")


class BuildError(Exception):
    """Raised when a build fails."""

    pass


class CloneError(Exception):
    """Raised when cloning a repository fails."""

    pass


# TODO: support switching to branch build job is scheduled for


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


def run(payload: Job) -> None:
    """
    Clone and run a script in an isolated temp directory.

    Args:
        repo: Git repository URL.

    Raises:
        CloneError: If cloning fails.
        BuildError: If script execution fails.
    """
    build_dir = Path(tempfile.mkdtemp(prefix="job_"))
    logger.info("Created temp build directory: %s", build_dir)

    try:
        clone_repo(payload.git_repository_url, build_dir)
        _run_script(payload.script, build_dir)
    except (CloneError, BuildError):
        utils.cleanup_build_files(build_dir)
        raise
