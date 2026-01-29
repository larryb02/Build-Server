import logging
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
        import subprocess

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
