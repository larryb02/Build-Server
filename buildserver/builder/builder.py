import os
import enum
import subprocess
import logging
from pathlib import Path
import re

import buildserver.config as config


class BuildStatus(enum.Enum):
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"


class Builder:
    BUILD_CMD = "make"
    BUILD_DIR = Path(config.BUILD_DIR).resolve()

    def __init__(self):
        logging.basicConfig()
        self.logger = logging.getLogger(
            f"{__name__}"
        )  # log format will be [MODULE: MSG]
        self.logger.setLevel(config.LOG_LEVEL)  # grab from config

    def clone_repo(self, repo: str):
        """
        Clone git repository into build directory

        params:
            repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
        raises:
            OSError
            CalledProcessError
        """
        self.logger.info("Cloning %s into %s", repo, Builder.BUILD_DIR)
        try:
            os.chdir(Builder.BUILD_DIR)
        except OSError as e:
            self.logger.error("Failed to change directory: %s", e.strerror)
            raise e
        subprocess.run(["/usr/bin/git", "clone", repo], check=True)
        try:
            commit_hash = self.get_commit_hash(Path.cwd())
        except Exception as e:
            self.logger.error(f"Failed to get commit hash: {e}")
        self.logger.info(f"Cloned {repo} at {commit_hash} PWD: {Path.cwd()}")
        return commit_hash

    def build(self, repo: str):
        """
        Compile C program into a binary

        params:
            repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
        raises:
            OSError
            CalledProcessError
        """
        self.logger.info("Building %s")
        try:
            os.chdir(Path(Builder.BUILD_DIR, repo))
        except OSError as e:
            self.logger.error(f"Failed to change directory: {e.strerror}")
            raise e
        subprocess.run(Builder.BUILD_CMD, check=True)

    def is_artifact(self, file_name: str):
        denylist = r"Makefile|.*\.(c|h)"
        pattern = re.compile(denylist)
        return not pattern.match(file_name)

    def gather_artifacts(self, repo_url: str):
        """
        Collect all artifacts from a successful build
        """
        # since we're focused on c programs its safe to assume artifacts are object files or the compiled binary
        # the build directory we must traverse will have the path $BUILD_DIR/repo_name
        path = Path(Builder.BUILD_DIR, get_dir_name(repo_url))
        ignore = set([".git"])
        if not path.exists():
            self.logger.error(f"Path: {path} doesn't exist")
        artifacts = []
        for root, dirs, files in path.walk():
            dirs[:] = [d for d in dirs if d not in ignore]
            artifacts = artifacts + [
                (root, file) for file in files if self.is_artifact(file)
            ]
        artifact_metadata = []
        for artifact in artifacts:
            root, file = artifact
            artifact = Path(root, file)
            artifact_metadata.append(
                {
                    "artifact_file_name": artifact.name,
                    "artifact_file_contents": artifact.read_bytes(),
                    "commit_hash": self.get_commit_hash(root),
                    "git_repository_url": repo_url,
                }
            )
        return artifact_metadata

    def get_commit_hash(self, path: Path) -> str:
        """
        Get commit hash of the checked out branch
        """
        try:
            os.chdir(path)
        except OSError as e:
            self.logger.error(
                f"chdir: {e}"
            )  # new logging format make sure to update rest of code
            raise e
        p = subprocess.run(
            ["/usr/bin/git", "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE
        )  # NOTE: consider using command pattern for all of these subproccess calls
        commit_hash = str(p.stdout, encoding="utf-8").strip("\n")
        return commit_hash

    def run(self, repo: str):
        """
        Clone and build C program

        params:
            repo: string with an expected format of a valid git protocol e.g. git@github.com:some-users/repository
        raises:
            OSError
            CalledProcessError
        """
        try:
            commit_hash = self.clone_repo(repo)
            build_path = get_dir_name(repo)
            self.build(build_path)
            status = BuildStatus.SUCCEEDED
        except Exception as e:
            self.logger.error("Failed to build program: %s", e)
            status = BuildStatus.FAILED
            raise e
        return {
            "git_repository_url": repo,
            "commit_hash": commit_hash,
            "status": status,
        }


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
        repo = url.split(":")[-1:].split(".")[0]  # remove the .git
    else:
        repo = url.split("com/")[-1:].split(".")[0]
    return repo
