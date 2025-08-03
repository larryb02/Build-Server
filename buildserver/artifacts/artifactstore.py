from pathlib import Path
import shutil
import logging
import re
import os

from buildserver import utils
import buildserver.config as config

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)

BUILD_DIR = Path(config.BUILD_DIR).resolve()

def gather_artifacts(repo_url: str):
    """
    Collect all artifacts from a successful build
    """
    # since we're focused on c programs its safe to assume artifacts are object files or the compiled binary
    # the build directory we must traverse will have the path $BUILD_DIR/repo_name
    path = Path(config.BUILD_DIR, utils.get_dir_name(repo_url))
    ignore = set([".git"])
    if not path.exists():
        logger.error(f"Path: {path} doesn't exist")
    artifacts = []
    for root, dirs, files in path.walk():
        dirs[:] = [d for d in dirs if d not in ignore]
        artifacts = artifacts + [(root, file) for file in files if is_artifact(file)]
    artifact_metadata = []
    for artifact in artifacts:
        root, file = artifact
        artifact = Path(root, file)
        commit_hash = utils.get_commit_hash(root, logger)
        artifact_path = store_in_repository(artifact, commit_hash)
        artifact_metadata.append(
            {
                "artifact_file_name": artifact.name,
                "artifact_path": artifact_path,
                "commit_hash": commit_hash,
                "git_repository_url": repo_url,
            }
        )

    return artifact_metadata


def store_in_repository(artifact, commit_hash):
    """
    Add artifact for a specific build to the artifact repository
    """
    artifact_directory = Path(config.ARTIFACT_REPOSITORY_ROOT, commit_hash)
    artifact_directory.mkdir(mode=0o754, exist_ok=True)
    os.chdir(artifact_directory)
    try:
        artifact_path = shutil.copy(src=artifact, dst=artifact_directory)
    except Exception as e:
        logger.error(f"{store_in_repository.__name__}: Failed to copy artifact: {e}")
    logger.debug(f"Artifact written to {artifact_path}")
    return artifact_path


def is_artifact(file_name: str):
    denylist = r"Makefile|.*\.(c|h)"
    pattern = re.compile(denylist)
    return not pattern.match(file_name)


def is_artifact(file_name: str):
    denylist = r"Makefile|.*\.(c|h)"
    pattern = re.compile(denylist)
    return not pattern.match(file_name)
