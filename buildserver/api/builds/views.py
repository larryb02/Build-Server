"""Job API endpoints"""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.exceptions import RequestValidationError

from buildserver.api.builds.models import JobCreate, JobRead
from buildserver.database.core import DbSession
from buildserver.api.builds.models import JobStatusUpdate
from buildserver.services.builds import (
    register_job,
    get_job_by_id,
    get_all_jobs,
    update_job_status,
)
from buildserver.config import Config

logger = logging.getLogger(__name__)
logger.setLevel(Config().LOG_LEVEL)

router = APIRouter(prefix="/jobs")


def validate(repo_url: str):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


@router.post("/register", response_model=JobRead)
def register(repo: JobCreate, dbsession: DbSession):
    """
    Registers a new program to be built
    """
    try:
        validate(repo.git_repository_url)
    except RequestValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        )
    return register_job(repo, dbsession)


@router.get("", response_model=list[JobRead])
async def get_jobs(dbsession: DbSession) -> list[JobRead]:
    """Retrieve all job records."""
    try:
        jobs = list(job._mapping for job in get_all_jobs(dbsession))
    except Exception as e:
        logger.error(f"Failed to get jobs: {e}")
    return jobs[:10]  # make sure to sort by date descending


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, dbsession: DbSession) -> JobRead:
    """Retrieve a single job by ID."""
    job = get_job_by_id(dbsession, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )
    return job


@router.patch("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: int,
    status_update: JobStatusUpdate,
    dbsession: DbSession,
) -> JobRead:
    """Update the status of an existing job."""
    job = update_job_status(dbsession, job_id, status_update.job_status)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )
    return job
