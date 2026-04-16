"""Integration tests for project and pipeline service functions"""

from unittest.mock import patch

import pytest
from sqlalchemy import insert, select

from ...api.pipelines.models import Pipeline, PipelineJob, PipelineStatus
from ...api.pipelines.service import assign_job, update_job_status
from ...api.projects.models import ProjectCreate
from ...api.projects.service import (
    create_project,
    get_all_projects,
    get_project_by_id,
    trigger_pipeline,
)
from ...pipeline.spec import JobSpec, PipelineSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project(dbsession, name="My Repo", url="https://github.com/user/repo.git"):
    return create_project(ProjectCreate(name=name, git_repository_url=url), dbsession)


def _make_pipeline(dbsession, project_id, commit_hash="abc123", branch="main"):
    return dbsession.scalars(
        insert(Pipeline)
        .values(
            project_id=project_id,
            branch=branch,
            commit_hash=commit_hash,
            status=PipelineStatus.QUEUED,
        )
        .returning(Pipeline)
    ).one()


def _make_job(dbsession, pipeline_id, command="echo hi", status=PipelineStatus.QUEUED):
    return dbsession.scalars(
        insert(PipelineJob)
        .values(
            pipeline_id=pipeline_id,
            name="build",
            commands=command,
            status=status,
        )
        .returning(PipelineJob)
    ).one()


def _pipeline_status(dbsession, pipeline_id):
    return dbsession.get(Pipeline, pipeline_id).status


# ---------------------------------------------------------------------------
# Project service
# ---------------------------------------------------------------------------


class TestCreateProject:

    def test_creates_and_returns_project(self, dbsession):
        project = _make_project(dbsession)

        assert project.project_id is not None
        assert project.name == "My Repo"
        assert project.git_repository_url == "https://github.com/user/repo.git"

    def test_duplicate_url_raises(self, dbsession):
        _make_project(dbsession)
        dbsession.commit()

        with pytest.raises(Exception):
            _make_project(dbsession)
            dbsession.commit()


class TestGetAllProjects:

    def test_returns_empty_list_when_none(self, dbsession):
        assert get_all_projects(dbsession) == []

    def test_returns_all_projects(self, dbsession):
        _make_project(dbsession, url="https://github.com/user/repo1.git")
        _make_project(dbsession, url="https://github.com/user/repo2.git")
        dbsession.commit()

        result = get_all_projects(dbsession)

        assert len(result) == 2


class TestGetProjectById:

    def test_returns_project_when_exists(self, dbsession):
        project = _make_project(dbsession)
        dbsession.commit()

        result = get_project_by_id(project.project_id, dbsession)

        assert result is not None
        assert result.project_id == project.project_id

    def test_returns_none_when_not_exists(self, dbsession):
        assert get_project_by_id(999, dbsession) is None


# ---------------------------------------------------------------------------
# Trigger pipeline
# ---------------------------------------------------------------------------


_TWO_JOB_SPEC = PipelineSpec(
    jobs=[
        JobSpec(name="build", commands="pip install -r requirements.txt && pytest"),
        JobSpec(name="deploy", commands="./deploy.sh"),
    ]
)


class TestTriggerPipeline:

    @patch("buildserver.api.projects.service.get_remote_hash", return_value="deadbeef")
    @patch("buildserver.api.projects.service.parse_spec", return_value=_TWO_JOB_SPEC)
    def test_creates_pipeline_and_jobs(self, _spec, _hash, dbsession):
        project = _make_project(dbsession)
        dbsession.commit()

        pipeline = trigger_pipeline(project, "main", dbsession)
        dbsession.commit()

        assert pipeline.pipeline_id is not None
        assert pipeline.commit_hash == "deadbeef"
        assert pipeline.branch == "main"
        assert pipeline.status == PipelineStatus.QUEUED

        jobs = list(
            dbsession.scalars(
                select(PipelineJob).where(
                    PipelineJob.pipeline_id == pipeline.pipeline_id
                )
            ).all()
        )
        assert len(jobs) == 2

        names = {j.name for j in jobs}
        assert names == {"build", "deploy"}

        build_job = next(j for j in jobs if j.name == "build")
        assert build_job.commands == "pip install -r requirements.txt && pytest"
        assert build_job.status == PipelineStatus.QUEUED


# ---------------------------------------------------------------------------
# Job service — assign and pipeline status rollup
# ---------------------------------------------------------------------------


@pytest.mark.skip("these tests need to mock a runner")
class TestAssignJob:

    def test_assigns_oldest_queued_job(self, dbsession):
        project = _make_project(dbsession)
        dbsession.commit()
        pipeline = _make_pipeline(dbsession, project.project_id)
        dbsession.commit()
        job1 = _make_job(dbsession, pipeline.pipeline_id)
        _make_job(dbsession, pipeline.pipeline_id)
        dbsession.commit()

        assigned = assign_job(runner_id=1, dbsession=dbsession)

        assert assigned is not None
        assert assigned.pipeline_job_id == job1.pipeline_job_id
        assert assigned.runner_id == 1

    def test_returns_none_when_no_queued_jobs(self, dbsession):
        assert assign_job(runner_id=1, dbsession=dbsession) is None

    def test_does_not_assign_already_assigned_job(self, dbsession):
        project = _make_project(dbsession)
        dbsession.commit()
        pipeline = _make_pipeline(dbsession, project.project_id)
        dbsession.commit()
        _make_job(dbsession, pipeline.pipeline_id)
        dbsession.commit()

        assign_job(runner_id=1, dbsession=dbsession)
        dbsession.commit()

        assert assign_job(runner_id=2, dbsession=dbsession) is None


class TestUpdateJobStatusRollup:

    def _setup(self, dbsession, num_jobs=2):
        project = _make_project(dbsession)
        dbsession.commit()
        pipeline = _make_pipeline(dbsession, project.project_id)
        dbsession.commit()
        jobs = [_make_job(dbsession, pipeline.pipeline_id) for _ in range(num_jobs)]
        dbsession.commit()
        return pipeline, jobs

    def test_first_running_job_moves_pipeline_to_running(self, dbsession):
        pipeline, jobs = self._setup(dbsession)

        update_job_status(dbsession, jobs[0].pipeline_job_id, PipelineStatus.RUNNING)
        dbsession.commit()

        assert (
            _pipeline_status(dbsession, pipeline.pipeline_id) == PipelineStatus.RUNNING
        )

    def test_pipeline_stays_queued_when_only_one_of_two_jobs_terminal(self, dbsession):
        pipeline, jobs = self._setup(dbsession)

        update_job_status(dbsession, jobs[0].pipeline_job_id, PipelineStatus.SUCCEEDED)
        dbsession.commit()

        assert (
            _pipeline_status(dbsession, pipeline.pipeline_id) == PipelineStatus.QUEUED
        )

    def test_all_succeeded_rolls_up_to_succeeded(self, dbsession):
        pipeline, jobs = self._setup(dbsession)

        update_job_status(dbsession, jobs[0].pipeline_job_id, PipelineStatus.SUCCEEDED)
        update_job_status(dbsession, jobs[1].pipeline_job_id, PipelineStatus.SUCCEEDED)
        dbsession.commit()

        assert (
            _pipeline_status(dbsession, pipeline.pipeline_id)
            == PipelineStatus.SUCCEEDED
        )

    def test_any_failed_rolls_up_to_failed(self, dbsession):
        pipeline, jobs = self._setup(dbsession)

        update_job_status(dbsession, jobs[0].pipeline_job_id, PipelineStatus.SUCCEEDED)
        update_job_status(dbsession, jobs[1].pipeline_job_id, PipelineStatus.FAILED)
        dbsession.commit()

        assert (
            _pipeline_status(dbsession, pipeline.pipeline_id) == PipelineStatus.FAILED
        )

    def test_single_job_pipeline_rolls_up_on_success(self, dbsession):
        pipeline, jobs = self._setup(dbsession, num_jobs=1)

        update_job_status(dbsession, jobs[0].pipeline_job_id, PipelineStatus.SUCCEEDED)
        dbsession.commit()

        assert (
            _pipeline_status(dbsession, pipeline.pipeline_id)
            == PipelineStatus.SUCCEEDED
        )

    def test_returns_none_for_nonexistent_job(self, dbsession):
        assert update_job_status(dbsession, 999, PipelineStatus.RUNNING) is None
