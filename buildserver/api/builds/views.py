"""Build API endpoints"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError

from buildserver.agent.agent import JobType
from buildserver.api.builds.models import BuildCreate, BuildRead
from buildserver.database.core import DbSession
from buildserver.services.builds import register, get_all_builds

router = APIRouter(prefix="/builds")


def validate(repo_url: str):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


@router.post("/register", response_model=BuildRead)
async def register_build(
    repo: BuildCreate,
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
    build = await register(repo)
    await request.state.agent.add_job(
        JobType.BUILD_PROGRAM, (repo.git_repository_url, build.build_id)
    )
    return {
        "git_repository_url": build.git_repository_url,
        "build_id": build.build_id,
        "commit_hash": build.commit_hash,
        "build_status": build.build_status,
        "created_at": build.created_at,
    }


@router.get("", response_model=list[BuildRead])
async def get_builds(dbsession: DbSession, request: Request):
    try:
        builds = list(build._mapping for build in get_all_builds(dbsession))
    except Exception as e:
        request.state.logger.error(f"Failed to get build: {e}")
    return builds[:10]  # make sure to sort by date descending
