"""Job service layer for database operations"""

import logging

from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from ...database.core import DbSession
from .models import (
    Artifact,
    ArtifactCreate,
    Pipeline,
    PipelineJob,
    PipelineJobRead,
    PipelineStatus,
)

logger = logging.getLogger(__name__)

_TERMINAL = {PipelineStatus.SUCCEEDED, PipelineStatus.FAILED}


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
        # At least one job is still QUEUED or RUNNING — not done yet.
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


def get_all_jobs(dbsession: DbSession) -> list[PipelineJob]:
    try:
        return list(dbsession.scalars(select(PipelineJob)).all())
    except DBAPIError as exc:
        logger.error("get_all_jobs: %s", exc)
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
