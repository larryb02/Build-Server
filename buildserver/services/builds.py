"""Job service layer for database operations"""

import logging

from sqlalchemy import insert, or_, select, update

from buildserver.config import Config
from buildserver.database.core import DbSession, create_session
from buildserver.models.jobs import JobStatus
from buildserver.api.builds.models import (
    Artifact,
    ArtifactCreate,
    Job,
    JobCreate,
    JobRead,
)
from buildserver.rmq.rmq import RabbitMQProducer

config = Config()


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


def register_job(repo: JobCreate) -> JobRead:
    """
    Register a new job and create a database record with QUEUED status.
    """
    dbsession = create_session()
    try:
        job = JobRead(**dict(create_job(repo, dbsession)._mapping))
        dbsession.commit()
        # publish to queue
        publisher = RabbitMQProducer()
        publisher.publish(
            "build_queue", bytes(JobRead)
        )  # fix this later, types are all fucked up right now
        return job
    except Exception as e:
        logger.error("Failed to write job to db: %s", e)
        dbsession.rollback()
    dbsession.close()


def get_all_jobs(dbsession: DbSession):
    """Retrieve all job records from the database."""
    stmt = select(*Job.__table__.columns)
    try:
        records = dbsession.execute(stmt).fetchall()
    except Exception as e:
        raise e
    return records


def create_job(job: JobCreate, dbsession: DbSession):
    """Insert a new job record into the database."""
    stmt = (
        insert(Job)
        .values(git_repository_url=job.git_repository_url, job_status=JobStatus.QUEUED)
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


def get_all_unique_jobs() -> list[JobRead]:
    """
    Retrieve the most recent job for each unique repository URL.

    A job is considered unique if its git_repository_url differs from others.
    Only includes jobs with SUCCEEDED or FAILED status.
    """
    db_session = create_session()
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
    jobs = db_session.execute(stmt).fetchall()
    jobs = [JobRead(**job._mapping) for job in jobs]
    db_session.close()
    return jobs
