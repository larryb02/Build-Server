import pytest
from datetime import datetime

from runner.builder.builder import ShellBuilder, _run_script, CloneError, BuildError
from runner.types import Job, JobStatus


def _make_job(**kwargs) -> Job:
    defaults = dict(
        job_id=1,
        git_repository_url="https://github.com/larryb02/test.git",
        commit_hash=None,
        job_status=JobStatus.QUEUED,
        created_at=datetime.now(),
    )
    return Job(**{**defaults, **kwargs})


class TestRunScript:
    def test_script_not_found(self, tmp_path):
        with pytest.raises(BuildError):
            _run_script(tmp_path / "missing.sh")

    def test_script_pass(self, tmp_path):
        script = tmp_path / ".buildserver.sh"
        script.write_text("#!/bin/bash\nexit 0\n")
        _run_script(script)

    def test_script_fail(self, tmp_path):
        script = tmp_path / ".buildserver.sh"
        script.write_text("#!/bin/bash\nexit 1\n")
        with pytest.raises(BuildError):
            _run_script(script)


@pytest.mark.skip("skip until I create an environment where CI can invoke git.")
class TestShellBuilder:

    def test_clone_http(self, tmp_path):
        job = _make_job(git_repository_url="https://github.com/larryb02/test.git")
        builder = ShellBuilder(job)
        builder.prepare_environment()
        assert builder.repo_dir.exists()

    def test_clone_invalid_repo(self):
        job = _make_job(git_repository_url="https://github.com:nonexistent/repo.git")
        builder = ShellBuilder(job)
        with pytest.raises(CloneError):
            builder.prepare_environment()

    def test_run_build_success(self):
        job = _make_job(git_repository_url="git@github.com:larryb02/test.git")
        ShellBuilder(job).run()

    def test_run_clone_failure(self):
        job = _make_job(git_repository_url="git@github.com:nonexistent/repo.git")
        with pytest.raises(CloneError):
            ShellBuilder(job).run()
