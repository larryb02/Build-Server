import logging
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from buildserver import utils


class TestGetDirName:

    def test_git_ssh_url(self):
        url = "git@github.com:some-user/my-repo.git"
        assert utils.get_dir_name(url) == "my-repo"

    def test_https_url(self):
        url = "https://github.com/some-user/my-repo.git"
        assert utils.get_dir_name(url) == "my-repo"

    def test_local_directory(self, tmp_path):
        local_dir = tmp_path / "my-project"
        local_dir.mkdir()
        assert utils.get_dir_name(str(local_dir)) == "my-project"

    def test_git_url_no_extension(self):
        url = "git@github.com:some-user/repo-name.git"
        assert utils.get_dir_name(url) == "repo-name"


class TestGetCommitHash:

    def test_returns_commit_hash(self, tmp_path):
        # Initialize a git repo with a commit
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], check=True)
        test_file = repo / "file.txt"
        test_file.write_text("hello")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "init"],
            check=True,
            env={
                "GIT_AUTHOR_NAME": "test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "test",
                "GIT_COMMITTER_EMAIL": "test@test.com",
                "HOME": str(tmp_path),
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin",
            },
        )
        log = logging.getLogger("test")
        commit_hash = utils.get_commit_hash(repo, log)
        assert len(commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in commit_hash)

    def test_invalid_path_raises(self, tmp_path):
        log = logging.getLogger("test")
        with pytest.raises(OSError):
            utils.get_commit_hash(tmp_path / "nonexistent", log)


class TestGetRemoteHash:

    @patch("buildserver.utils.subprocess.run")
    def test_returns_hash(self, mock_run):
        expected_hash = "a" * 40
        mock_run.return_value = MagicMock(stdout=f"{expected_hash}\tHEAD".encode())

        result = utils.get_remote_hash("git@github.com:user/repo.git")

        assert result == expected_hash
        mock_run.assert_called_once_with(
            ["/usr/bin/git", "ls-remote", "git@github.com:user/repo.git", "HEAD"],
            stdout=subprocess.PIPE,
            check=True,
        )

    @patch("buildserver.utils.subprocess.run")
    def test_raises_on_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        with pytest.raises(subprocess.CalledProcessError):
            utils.get_remote_hash("git@github.com:user/repo.git")


class TestCompareHashes:

    def test_matching_hashes(self):
        hash = "a" * 40
        assert utils.compare_hashes(hash, hash) is True

    def test_different_hashes(self):
        assert utils.compare_hashes("a" * 40, "b" * 40) is False


class TestCleanupBuildFiles:

    def test_removes_directory(self, tmp_path):
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "artifact").write_text("data")
        utils.cleanup_build_files(build_dir)
        assert not build_dir.exists()

    def test_nonexistent_path_does_not_raise(self, tmp_path):
        # Should log error but not raise
        utils.cleanup_build_files(tmp_path / "nonexistent")
