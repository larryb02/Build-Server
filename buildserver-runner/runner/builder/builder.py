"""Clone a repository at a specific commit and execute a shell command."""

import logging
import subprocess
import tempfile
from pathlib import Path

import git

from runner.config import LOG_LEVEL
from runner.types import PipelineJob

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class BuildError(Exception):
    """Raised when command execution fails."""


class CloneError(Exception):
    """Raised when cloning or checking out a repository fails."""


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


def run(payload: PipelineJob) -> None:
    """
    Clone the repository at the job's commit and execute its commands in order.

    Raises:
        CloneError: If cloning fails.
        BuildError: If any command exits with a non-zero code.
    """
    with tempfile.TemporaryDirectory(prefix="job_") as tmp:
        build_dir = Path(tmp)
        logger.info("Job %s: build dir %s", payload.pipeline_job_id, build_dir)
        repo_dir = clone_repo(
            payload.git_repository_url, payload.commit_hash, build_dir
        )
        for command in payload.commands:
            run_command(command, repo_dir)
