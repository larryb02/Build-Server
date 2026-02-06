"""Job API endpoints"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError

from buildserver.api.builds.models import JobCreate, JobRead
from buildserver.database.core import DbSession
from buildserver.models.jobs import JobStatusUpdate
from buildserver.services.builds import register_job, get_all_jobs, update_job_status

router = APIRouter(prefix="/jobs")


def validate(repo_url: str):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


@router.post("/register", response_model=JobRead)
async def register_build(
    repo: JobCreate,
    request: Request,
):
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
    # build = await register(repo)
    # await request.state.agent.add_job(
    #     JobType.BUILD_PROGRAM, (repo.git_repository_url, build.build_id)
    # )
    # return {
    #     "git_repository_url": build.git_repository_url,
    #     "build_id": build.build_id,
    #     "commit_hash": build.commit_hash,
    #     "build_status": build.build_status,
    #     "created_at": build.created_at,
    # }


@router.get("", response_model=list[JobRead])
async def get_jobs(dbsession: DbSession, request: Request) -> list[JobRead]:
    """Retrieve all job records."""
    try:
        jobs = list(job._mapping for job in get_all_jobs(dbsession))
    except Exception as e:
        request.state.logger.error(f"Failed to get jobs: {e}")
    return jobs[:10]  # make sure to sort by date descending


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
