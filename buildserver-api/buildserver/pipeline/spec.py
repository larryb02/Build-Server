"""
Clone a repository at a specific commit, parse its .buildserver.yaml spec,
and return a structured representation for pipeline creation.
"""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

import git
import yaml

logger = logging.getLogger(__name__)

SPEC_FILE = ".buildserver.yaml"


@dataclass
class JobSpec:
    name: str
    commands: list[str]


@dataclass
class PipelineSpec:
    jobs: list[JobSpec]


class SpecError(Exception):
    """Raised when the pipeline spec is missing or malformed."""


def parse_spec(repo_url: str, commit_hash: str) -> PipelineSpec:
    """
    Clone repo at commit_hash into a temp directory, parse .buildserver.yaml,
    then discard the clone.

    Args:
        repo_url: Git repository URL.
        commit_hash: Commit to check out.

    Returns:
        PipelineSpec with ordered list of JobSpecs.

    Raises:
        SpecError: If cloning, checkout, or parsing fails.
    """
    with tempfile.TemporaryDirectory(prefix="spec_") as tmp:
        repo_dir = Path(tmp) / "repo"
        logger.info("Cloning %s at %s for spec parsing", repo_url, commit_hash)
        try:
            repo = git.Repo.clone_from(repo_url, repo_dir)
            repo.git.checkout(commit_hash)
        except git.GitCommandError as e:
            raise SpecError(
                f"Failed to clone/checkout {repo_url}@{commit_hash}: {e}"
            ) from e

        spec_path = repo_dir / SPEC_FILE
        if not spec_path.exists():
            raise SpecError(f"{SPEC_FILE} not found in {repo_url}@{commit_hash}")

        try:
            raw = yaml.safe_load(spec_path.read_text())
        except yaml.YAMLError as e:
            raise SpecError(f"Failed to parse {SPEC_FILE}: {e}") from e

    return _parse_raw(raw)


def _parse_raw(raw: dict) -> PipelineSpec:
    if not isinstance(raw, dict) or "jobs" not in raw:
        raise SpecError("Spec must have a top-level 'jobs' key")

    if not raw["jobs"]:
        raise SpecError("Spec must define at least one job")

    jobs = []
    logger.debug("raw content: %s", raw)
    for name, cfg in raw["jobs"].items():
        if not isinstance(cfg, dict) or "steps" not in cfg:
            raise SpecError(f"Job '{name}' must have a 'steps' key")
        if not isinstance(cfg["steps"], list) or not cfg["steps"]:
            raise SpecError(f"Job '{name}': 'steps' must be a non-empty list")
        commands = []
        for step in cfg["steps"]:
            if not isinstance(step, dict) or "run" not in step:
                raise SpecError(f"Job '{name}': each step must have a 'run' key")
            if not isinstance(step["run"], str):
                raise SpecError(f"Job '{name}': 'run' must be a string")
            commands.append(step["run"])
        jobs.append(JobSpec(name=name, commands=commands))

    return PipelineSpec(jobs=jobs)
