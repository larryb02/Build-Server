"""Integration tests for builds service functions"""

from buildserver.api.builds.models import JobCreate
from buildserver.api.builds.models import JobStatus
from buildserver.services.builds import (
    create_job,
    get_job_by_id,
    get_all_jobs,
    update_job_status,
)


class TestGetJobById:

    def test_returns_job_when_exists(self, dbsession):
        job_create = JobCreate(git_repository_url="git@github.com:user/repo.git")
        created = create_job(job_create, dbsession)
        dbsession.commit()

        result = get_job_by_id(dbsession, created.job_id)

        assert result is not None
        assert result.job_id == created.job_id
        assert result.git_repository_url == "git@github.com:user/repo.git"
        assert result.job_status == JobStatus.QUEUED

    def test_returns_none_when_not_exists(self, dbsession):
        result = get_job_by_id(dbsession, 999)

        assert result is None


class TestCreateJob:

    def test_creates_job_with_queued_status(self, dbsession):
        job_create = JobCreate(git_repository_url="git@github.com:user/repo.git")

        result = create_job(job_create, dbsession)
        dbsession.commit()

        assert result is not None
        assert result.job_id is not None
        assert result.git_repository_url == "git@github.com:user/repo.git"
        assert result.job_status == JobStatus.QUEUED


class TestGetAllJobs:

    def test_returns_empty_list_when_no_jobs(self, dbsession):
        result = get_all_jobs(dbsession)

        assert result == []

    def test_returns_all_jobs(self, dbsession):
        job1 = JobCreate(git_repository_url="git@github.com:user/repo1.git")
        job2 = JobCreate(git_repository_url="git@github.com:user/repo2.git")
        create_job(job1, dbsession)
        create_job(job2, dbsession)
        dbsession.commit()

        result = get_all_jobs(dbsession)

        assert len(result) == 2


class TestUpdateJobStatus:

    def test_updates_status(self, dbsession):
        job_create = JobCreate(git_repository_url="git@github.com:user/repo.git")
        created = create_job(job_create, dbsession)
        dbsession.commit()

        result = update_job_status(dbsession, created.job_id, JobStatus.RUNNING)

        assert result is not None
        assert result.job_status == JobStatus.RUNNING

    def test_returns_none_when_job_not_exists(self, dbsession):
        result = update_job_status(dbsession, 999, JobStatus.RUNNING)

        assert result is None
