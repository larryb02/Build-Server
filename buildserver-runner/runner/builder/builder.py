"""
Functions for compiling C programs
"""

import os
import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import git

from runner import utils
from runner.config import LOG_LEVEL
from runner.types import Job

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

SCRIPT_FILE = ".buildserver.sh"


class Builder(ABC):
    """Interface for runner execution environments."""

    @abstractmethod
    def prepare_environment(self) -> None: ...

    @abstractmethod
    def run(self) -> None: ...


class ShellBuilder(Builder):
    """Executes a job on the local system shell."""

    def __init__(self, job: Job) -> None:
        self.job = job
        self.build_dir: Path | None = None
        self.repo_dir: Path | None = None

    def prepare_environment(self) -> None:
        """Create a temp directory, clone the repo, and checkout the target commit."""
        self.build_dir = Path(tempfile.mkdtemp(prefix="job_"))
        logger.info("Created build directory: %s", self.build_dir)

        repo_name = utils.get_dir_name(self.job.git_repository_url)
        self.repo_dir = self.build_dir / repo_name

        logger.info("Cloning %s", self.job.git_repository_url)
        try:
            cloned = git.Repo.clone_from(self.job.git_repository_url, self.repo_dir)
        except git.GitCommandError as e:
            raise CloneError(
                f"Failed to clone {self.job.git_repository_url}: {e}"
            ) from e

        if self.job.commit_hash:
            try:
                cloned.git.checkout(self.job.commit_hash)
            except git.GitCommandError as e:
                raise CloneError(
                    f"Failed to checkout {self.job.commit_hash}: {e}"
                ) from e

        actual_hash = cloned.head.commit.hexsha
        logger.info("Cloned %s at %s", repo_name, actual_hash)

        os.environ["JOB_ID"] = str(self.job.job_id)
        os.environ["REPO_URL"] = self.job.git_repository_url
        os.environ["COMMIT_HASH"] = actual_hash

    def run(self) -> None:
        """Prepare the environment and execute the build script."""
        try:
            self.prepare_environment()
            _run_script(self.repo_dir / SCRIPT_FILE, self.repo_dir)
        except (CloneError, BuildError):
            if self.build_dir:
                utils.cleanup_build_files(self.build_dir)
            raise


def _run_script(script_path: Path, cwd: Path = None):
    if not script_path.exists():
        raise BuildError(f"Build script not found: {script_path}")

    os.chmod(script_path, 0o755)

    with subprocess.Popen(
        ["/bin/bash", str(script_path)],
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


class CloneError(Exception):
    """Raised when cloning a repository fails."""


# TODO: support switching to branch build job is scheduled for


# def clone_repo(repo: str, build_dir: Path) -> str:
#     """
#     Clone git repository into build directory.

#     Args:
#         repo: Git repository URL (git@ or https://)
#         build_dir: Directory to clone into

#     Returns:
#         The commit hash of the cloned repo.

#     Raises:
#         CloneError: If cloning fails.
#     """
#     logger.info("Cloning %s into %s", repo, build_dir)
#     try:
#         result = subprocess.run(
#             ["/usr/bin/git", "clone", repo],
#             cwd=build_dir,
#             check=True,
#             capture_output=True,
#             text=True,
#         )
#     except subprocess.CalledProcessError as e:
#         raise CloneError(f"Failed to clone {repo}: {e.stderr}") from e

#     repo_name = utils.get_dir_name(repo)
#     repo_path = build_dir / repo_name

#     try:
#         commit_hash = utils.get_commit_hash(repo_path, logger)
#     except Exception as e:
#         raise CloneError(f"Failed to get commit hash: {e}") from e

#     logger.info("Cloned %s at %s", repo_name, commit_hash)
#     return commit_hash


# def run(payload: Job) -> None:
#     """
#     Clone and run a script in an isolated temp directory.

#     Args:
#         repo: Git repository URL.

#     Raises:
#         CloneError: If cloning fails.
#         BuildError: If script execution fails.
#     """
#     build_dir = Path(tempfile.mkdtemp(prefix="job_"))
#     logger.info("Created temp build directory: %s", build_dir)

#     try:
#         clone_repo(payload.git_repository_url, build_dir)
#         repo_dir = build_dir / utils.get_dir_name(payload.git_repository_url)
#         _run_script(repo_dir / SCRIPT_FILE, repo_dir)
#     except (CloneError, BuildError):
#         utils.cleanup_build_files(build_dir)
#         raise
