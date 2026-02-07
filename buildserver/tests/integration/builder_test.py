import pytest

from buildserver.agent.builder.builder import (
    clone_repo,
    run,
    CloneError,
)


pytestmark = pytest.mark.skip(
    "skip until I create an environment where CI can invoke git."
)


class TestCloneRepo:

    def test_clone_git(self, tmp_path):
        git_repo_url = "git@github.com:larryb02/test.git"
        clone_repo(git_repo_url, tmp_path)
        assert (tmp_path / "test").exists()

    def test_clone_http(self, tmp_path):
        http_repo_url = "https://github.com/larryb02/test.git"
        clone_repo(http_repo_url, tmp_path)
        assert (tmp_path / "test").exists()

    def test_clone_invalid_repo(self, tmp_path):
        invalid_repo = "git@github.com:nonexistent/repo.git"
        with pytest.raises(CloneError):
            clone_repo(invalid_repo, tmp_path)


class TestRun:

    def test_run_build_success(self):
        test_repo = "git@github.com:larryb02/test.git"
        # Should not raise
        run(test_repo)

    def test_run_clone_failure(self):
        invalid_repo = "git@github.com:nonexistent/repo.git"
        with pytest.raises(CloneError):
            run(invalid_repo)
