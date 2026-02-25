import pytest

from runner.builder.builder import clone_repo, run, _run_script, CloneError, BuildError


class TestRunScript:
    def test_empty_script(self):
        _run_script("")

    def test_script_pass(self):
        _run_script("exit 0\n")

    def test_script_fail(self):
        with pytest.raises(BuildError):
            _run_script("exit 1\n")


@pytest.mark.skip("skip until I create an environment where CI can invoke git.")
class TestCloneRepo:

    def test_clone_http(self, tmp_path):
        http_repo_url = "https://github.com/larryb02/test.git"
        clone_repo(http_repo_url, tmp_path)
        assert (tmp_path / "test").exists()

    def test_clone_invalid_repo(self, tmp_path):
        invalid_repo = "https://github.com:nonexistent/repo.git"
        with pytest.raises(CloneError):
            clone_repo(invalid_repo, tmp_path)


@pytest.mark.skip("skip until I create an environment where CI can invoke git.")
class TestRun:

    def test_run_build_success(self):
        test_repo = "git@github.com:larryb02/test.git"
        # Should not raise
        run(test_repo)

    def test_run_clone_failure(self):
        invalid_repo = "git@github.com:nonexistent/repo.git"
        with pytest.raises(CloneError):
            run(invalid_repo)
