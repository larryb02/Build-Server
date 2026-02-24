"""Job service layer for database operations"""

import logging

from fastapi.exceptions import RequestValidationError
from sqlalchemy import insert, or_, select, update

from buildserver.config import LOG_LEVEL
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
from buildserver.rmq.rmq import RabbitMQProducer

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def validate(repo_url: str):
    if repo_url == "":
        raise ValueError("Url may not be blank")
    if not repo_url.startswith("https://"):
        raise ValueError("Url must be https protocol")


def get_job_by_id(dbsession: DbSession, job_id: int) -> JobRead | None:
    """Retrieve a single job by ID."""
    stmt = select(*Job.__table__.columns).where(Job.job_id == job_id)
    record = dbsession.execute(stmt).one_or_none()
    if record is None:
        return None
    return JobRead(**record._mapping)


def get_all_jobs(dbsession: DbSession):
    """Retrieve all job records from the database."""
    stmt = select(*Job.__table__.columns)
    try:
        records = dbsession.execute(stmt).fetchall()
    except Exception as e:
        raise e
    return records


def create_job(job: JobCreate, dbsession: DbSession, commit_hash: str | None = None):
    """Insert a new job record into the database."""
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


def register_job(repo: JobCreate, dbsession: DbSession) -> JobRead:
    """Create a new job and publish it to the build queue."""
    commit_hash = get_remote_hash(repo.git_repository_url)
    job = JobRead(**dict(create_job(repo, dbsession, commit_hash)._mapping))
    publisher = RabbitMQProducer()
    publisher.publish("build_jobs", job.model_dump_json().encode())
    return job


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
