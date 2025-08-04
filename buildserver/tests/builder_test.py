from pathlib import Path
import pytest

import buildserver.builder.builder as builder
from buildserver import utils
from buildserver.config import BUILD_DIR


def test_build():
    build_repo = "../hello"
    builder.build(build_repo)  # no exceptions should be thrown here

    bad_build_repo = "../thisdoesntexist"
    with pytest.raises(OSError):
        builder.build(bad_build_repo)


def test_clone():
    git_repo_url = "git@github.com:rpm-software-management/dnf.git"
    builder.clone_repo(git_repo_url)
    # Repository should exist in $BUILD_DIR/repo
    assert Path(BUILD_DIR, "dnf").exists()
    utils.cleanup_build_files(Path(BUILD_DIR, "dnf"))

    http_repo_url = "https://github.com/rpm-software-management/dnf.git"
    builder.clone_repo(http_repo_url)
    assert Path(BUILD_DIR, "dnf").exists()
    utils.cleanup_build_files(Path(BUILD_DIR, "dnf"))


def test_run():
    # repo doesnt exist

    # build fail
    # # build success
    assert True
