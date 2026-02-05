from pathlib import Path
import pytest

from buildserver.builder import builder


@pytest.mark.skip("Work in progress")
class TestBuild:
    def test_build(self):
        build_repo = "../hello"
        builder.build(build_repo)

    def test_build_bad_repo(self):
        bad_build_repo = "../thisdoesntexist"
        with pytest.raises(OSError):
            builder.build(bad_build_repo)


class TestCloneRepo:

    def test_clone_git(self, tmp_path, monkeypatch):
        monkeypatch.setattr(builder, "BUILD_DIR", str(tmp_path))
        git_repo_url = "git@github.com:rpm-software-management/dnf.git"
        builder.clone_repo(git_repo_url)
        assert Path(tmp_path, "dnf").exists()

    def test_clone_http(self, tmp_path, monkeypatch):
        monkeypatch.setattr(builder, "BUILD_DIR", str(tmp_path))
        http_repo_url = "https://github.com/rpm-software-management/dnf.git"
        builder.clone_repo(http_repo_url)
        assert Path(tmp_path, "dnf").exists()


class TestRun:

    # TODO: make finer grained error handling: script errors, system errors, etc
    # also figure out why local repos aren't being found specifically in these tests?
    # def test_run_build_fail_script_error(self, tmp_path, monkeypatch):
    #     monkeypatch.setattr(builder, "BUILD_DIR", str(tmp_path))
    #     local_test_repo_broken = "./tests/local_repos/hello_fail"
    #     build = builder.run(local_test_repo_broken)
    #     assert build["build_status"] == builder.BuildStatus.FAILED

    def test_run_build_success(self, tmp_path, monkeypatch):
        monkeypatch.setattr(builder, "BUILD_DIR", str(tmp_path))
        local_test_repo = "git@github.com:larryb02/test.git"
        build = builder.run(local_test_repo)
        assert build["build_status"] == builder.BuildStatus.SUCCEEDED
