"""Clone a repository at a specific commit and execute a shell command."""

import logging
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import git

from runner import utils
from runner.config import LOG_LEVEL
from runner.types import PipelineJob

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class Builder(ABC):
    """Interface for runner execution environments."""

    @abstractmethod
    def prepare_environment(self) -> None: ...

    @abstractmethod
    def run(self) -> None: ...


class ShellBuilder(Builder):
    """Executes a job on the local system shell."""

    def __init__(self, job: PipelineJob) -> None:
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

    def run(self) -> None:
        """
        Clone the repository at the job's commit and execute its commands in order.

        Raises:
            CloneError: If cloning fails.
            BuildError: If any command exits with a non-zero code.
        """
        with tempfile.TemporaryDirectory(prefix="job_") as tmp:
            build_dir = Path(tmp)
            logger.info("Job %s: build dir %s", self.job.pipeline_job_id, build_dir)
            repo_dir = clone_repo(
                self.job.git_repository_url, self.job.commit_hash, build_dir
            )
            for command in self.job.commands:
                run_command(command, repo_dir)


def clone_repo(repo_url: str, commit_hash: str, build_dir: Path) -> Path:
    """
    Clone repo_url into build_dir and check out commit_hash.

    Returns:
        Path to the cloned repository root.

    Raises:
        CloneError: If cloning or checkout fails.
    """
    logger.info("Cloning %s at %s", repo_url, commit_hash)
    try:
        repo = git.Repo.clone_from(repo_url, build_dir / "repo")
        repo.git.checkout(commit_hash)
    except git.GitCommandError as exc:
        raise CloneError(
            f"Failed to clone/checkout {repo_url}@{commit_hash}: {exc}"
        ) from exc
    return build_dir / "repo"


def run_command(command: str, cwd: Path) -> None:
    """
    Execute a shell command in cwd, streaming output to the logger.

    Raises:
        BuildError: If the command exits with a non-zero code.
    """
    logger.info("Running: %s", command)
    with subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as proc:
        for line in proc.stdout:
            logger.info(line.rstrip())
    if proc.returncode != 0:
        raise BuildError(f"Command exited with code {proc.returncode}: {command}")


class BuildError(Exception):
    """Raised when a build fails."""


class CloneError(Exception):
    """Raised when cloning a repository fails."""


# TODO: support switching to branch build job is scheduled for
