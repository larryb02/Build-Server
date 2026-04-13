"""Service layer for Pipeline and PipelineJob database operations"""

import logging

from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from ...database.core import DbSession
from .models import (
    Artifact,
    ArtifactCreate,
    Pipeline,
    PipelineDetail,
    PipelineJob,
    PipelineJobRead,
    PipelineJobSummary,
    PipelineStatus,
)

logger = logging.getLogger(__name__)

_TERMINAL = {PipelineStatus.SUCCEEDED, PipelineStatus.FAILED}


# ---------------------------------------------------------------------------
# Pipeline queries
# ---------------------------------------------------------------------------


def get_all_pipelines(dbsession: DbSession) -> list[Pipeline]:
    try:
        return list(dbsession.scalars(select(Pipeline)).all())
    except DBAPIError as exc:
        logger.error("get_all_pipelines: %s", exc)
        raise


def get_pipeline_detail(
    pipeline_id: int, dbsession: DbSession
) -> PipelineDetail | None:
    """
    Fetch a pipeline and all its jobs in a single joined query.
    The join expands the single pipeline row into one row per job;
    we take the pipeline from the first row and collect jobs across all rows.
    """
    try:
        rows = dbsession.execute(
            select(Pipeline, PipelineJob)
            .join(PipelineJob, PipelineJob.pipeline_id == Pipeline.pipeline_id)
            .where(Pipeline.pipeline_id == pipeline_id)
        ).all()

        if not rows:
            return None

        pipeline, _ = rows[0]
        jobs = [job for _, job in rows]

        return PipelineDetail(
            pipeline_id=pipeline.pipeline_id,
            project_id=pipeline.project_id,
            branch=pipeline.branch,
            commit_hash=pipeline.commit_hash,
            status=PipelineStatus(pipeline.status),
            created_at=pipeline.created_at,
            jobs=[
                PipelineJobSummary(
                    pipeline_job_id=j.pipeline_job_id,
                    name=j.name,
                    status=PipelineStatus(j.status),
                    created_at=j.created_at,
                )
                for j in jobs
            ],
        )
    except DBAPIError as exc:
        logger.error("get_pipeline_detail: %s", exc)
        raise


# ---------------------------------------------------------------------------
# PipelineJob operations
# ---------------------------------------------------------------------------


def build_job_read(
    pipeline_job_id: int, dbsession: DbSession
) -> PipelineJobRead | None:
    """
    Build a PipelineJobRead for the given pipeline_job_id, joining to resolve
    repo URL and commit_hash from Project/Pipeline.
    """
    from ..projects.models import Project

    row = dbsession.execute(
        select(
            PipelineJob,
            Pipeline.commit_hash,
            Project.git_repository_url,
        )
        .join(Pipeline, PipelineJob.pipeline_id == Pipeline.pipeline_id)
        .join(Project, Pipeline.project_id == Project.project_id)
        .where(PipelineJob.pipeline_job_id == pipeline_job_id)
    ).one_or_none()

    if row is None:
        return None

    job, commit_hash, repo_url = row

    return PipelineJobRead(
        pipeline_job_id=job.pipeline_job_id,
        pipeline_id=job.pipeline_id,
        name=job.name,
        commands=job.commands,
        git_repository_url=repo_url,
        commit_hash=commit_hash,
        status=PipelineStatus(job.status),
        created_at=job.created_at,
    )


def _rollup_pipeline(pipeline_id: int, dbsession: DbSession) -> None:
    """Update Pipeline.status once all jobs have reached a terminal state."""
    statuses = set(
        dbsession.scalars(
            select(PipelineJob.status).where(PipelineJob.pipeline_id == pipeline_id)
        ).all()
    )

    if statuses - _TERMINAL:
        return

    final = (
        PipelineStatus.FAILED
        if PipelineStatus.FAILED in statuses
        else PipelineStatus.SUCCEEDED
    )
    dbsession.execute(
        update(Pipeline).where(Pipeline.pipeline_id == pipeline_id).values(status=final)
    )
    logger.info("Pipeline %s → %s", pipeline_id, final)


def assign_job(runner_id: int, dbsession: DbSession) -> PipelineJob | None:
    """Atomically assign the oldest queued job to a runner."""
    try:
        selected = (
            select(PipelineJob.pipeline_job_id)
            .where(PipelineJob.status == PipelineStatus.QUEUED)
            .where(PipelineJob.runner_id == None)  # noqa: E711
            .order_by(PipelineJob.created_at)
            .limit(1)
        )
        job = dbsession.scalars(
            update(PipelineJob)
            .where(PipelineJob.pipeline_job_id == selected)
            .values(runner_id=runner_id)
            .returning(PipelineJob)
        ).first()
        logger.debug("Assigned job %s to runner %s", job, runner_id)
        return job
    except DBAPIError as exc:
        logger.error("assign_job: %s", exc)
        raise


def get_job_by_id(pipeline_job_id: int, dbsession: DbSession) -> PipelineJobRead | None:
    try:
        return build_job_read(pipeline_job_id, dbsession)
    except DBAPIError as exc:
        logger.error("get_job_by_id: %s", exc)
        raise


def update_job_status(
    dbsession: DbSession, pipeline_job_id: int, new_status: PipelineStatus
) -> PipelineJob | None:
    try:
        job = dbsession.scalars(
            update(PipelineJob)
            .where(PipelineJob.pipeline_job_id == pipeline_job_id)
            .values(status=new_status)
            .returning(PipelineJob)
        ).first()

        if job is None:
            return None

        if new_status == PipelineStatus.RUNNING:
            dbsession.execute(
                update(Pipeline)
                .where(Pipeline.pipeline_id == job.pipeline_id)
                .where(Pipeline.status == PipelineStatus.QUEUED)
                .values(status=PipelineStatus.RUNNING)
            )
        elif new_status in _TERMINAL:
            _rollup_pipeline(job.pipeline_id, dbsession)

        return job
    except DBAPIError as exc:
        logger.error("update_job_status: %s", exc)
        raise


def create_artifact(artifact: ArtifactCreate, dbsession: DbSession):
    from sqlalchemy import insert

    try:
        stmt = (
            insert(Artifact)
            .values(
                artifact_file_name=artifact.artifact_file_name,
                git_repository_url=artifact.git_repository_url,
                commit_hash=artifact.commit_hash,
                artifact_path=artifact.artifact_path,
            )
            .returning(
                Artifact.artifact_id,
                Artifact.artifact_file_name,
                Artifact.commit_hash,
                Artifact.git_repository_url,
            )
        )
        return dbsession.execute(stmt).one_or_none()
    except DBAPIError as exc:
        logger.error("create_artifact: %s", exc)
        raise
