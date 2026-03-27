"""Job service layer for database operations"""

import logging

from sqlalchemy import insert, or_, select, update
from sqlalchemy.exc import DBAPIError

from buildserver.database.core import DbSession
from buildserver.api.jobs.models import JobStatus
from buildserver.api.jobs.models import (
    Artifact,
    ArtifactCreate,
    Job,
    JobCreate,
    JobRead,
)
from buildserver.utils import get_remote_hash

logger = logging.getLogger(__name__)


def assign_job(runner_id: int, dbsession: DbSession) -> Job | None:
    try:
        selected_job = (
            select(Job.job_id)
            .where(Job.job_status == JobStatus.QUEUED)
            .where(Job.runner_id == None)
            .limit(1)
        )
        job = dbsession.scalars(
            update(Job)
            .where(Job.job_id == selected_job)
            .values(runner_id=runner_id)
            .returning(Job)
        ).first()
        logger.debug("scheduling job %s to runner %s", job, runner_id)
        return job
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def get_available_jobs(dbsession: DbSession) -> list[Job]:
    try:
        res = dbsession.scalars(
            select(Job)
            .where(Job.job_status == JobStatus.QUEUED)
            .where(Job.runner_id == None)
        ).all()
        return list(res)
    except DBAPIError as exc:
        logger.debug(exc)
        raise exc


def validate(repo_url: str):
    if repo_url == "":
        raise ValueError("Url may not be blank")
    if not repo_url.startswith("https://"):
        raise ValueError("Url must be https protocol")


def get_job_by_id(job_id: int, dbsession: DbSession) -> Job | None:
    """Retrieve a single job by ID."""
    try:
        job = dbsession.get(Job, job_id)
        logger.debug("Got record: %s", job)
        return job
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def get_all_jobs(dbsession: DbSession):
    """Retrieve all job records from the database."""
    stmt = select(*Job.__table__.columns)
    try:
        records = dbsession.scalars(stmt).all()
        return records
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def create_job(job: JobCreate, dbsession: DbSession):
    """Insert a new job record into the database."""
    # NOTE: update this once runner receives? or set here
    commit_hash = get_remote_hash(job.git_repository_url)
    stmt = (
        insert(Job)
        .values(
            git_repository_url=job.git_repository_url,
            job_status=JobStatus.QUEUED,
            commit_hash=commit_hash,
        )
        .returning(
            Job.git_repository_url,
            Job.job_id,
            Job.job_status,
            Job.commit_hash,
            Job.created_at,
        )
    )
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record


# def register_job(repo: JobCreate, dbsession: DbSession) -> JobRead:
#     """Create a new job and publish it to the build queue."""
#     commit_hash = get_remote_hash(repo.git_repository_url)
#     job = JobRead(**create_job(repo, dbsession, commit_hash)._mapping)
#     return job


def create_artifact(artifact: ArtifactCreate, dbsession: DbSession):
    """Insert a new artifact record into the database."""
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
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record


def update_job_status(
    dbsession: DbSession, job_id: int, new_status: JobStatus
) -> JobRead | None:
    """
    Update the status of an existing job.

    Args:
        dbsession: Active database session.
        job_id: The ID of the job to update.
        new_status: The new status to set on the job.

    Returns:
        The updated job as a JobRead model, or None if the job was not found.
    """
    stmt = (
        update(Job)
        .where(Job.job_id == job_id)
        .values(job_status=new_status)
        .returning(*Job.__table__.columns)
    )
    record = dbsession.execute(stmt).one_or_none()
    if record is None:
        return None
    return JobRead(**record._mapping)


def get_all_unique_jobs(dbsession: DbSession) -> list[JobRead]:
    """
    Retrieve the most recent job for each unique repository URL.

    A job is considered unique if its git_repository_url differs from others.
    Only includes jobs with SUCCEEDED or FAILED status.

    TODO: service functions return data inconsistently — some return raw rows
    (get_all_jobs), some return JobRead models (get_all_unique_jobs, get_job_by_id).
    Standardize on one approach.
    """
    stmt = (
        select(*Job.__table__.columns)
        .distinct(Job.git_repository_url)
        .order_by(Job.git_repository_url, Job.created_at.desc())
        .where(
            or_(
                Job.job_status == JobStatus.SUCCEEDED,
                Job.job_status == JobStatus.FAILED,
            )
        )
    )
    jobs = dbsession.execute(stmt).fetchall()
    return [JobRead(**job._mapping) for job in jobs]
