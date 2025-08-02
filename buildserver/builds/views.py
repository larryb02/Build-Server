from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks
from fastapi.exceptions import RequestValidationError

from buildserver.builder.agent import Status
from buildserver.builds.models import BuildCreate, BuildRead
from buildserver.builds.service import create_build, validate, register, post_process
from buildserver.database.core import DbSession

router = APIRouter(prefix="/builds")


@router.post("/register", response_model=BuildRead)
async def register_build(
    repo: BuildCreate,
    background_tasks: BackgroundTasks,
    dbsession: DbSession,
    request: Request,
):
    """
    Registers a new program to be built
    """
    git_url = repo.git_repository_url
    try:
        validate(git_url)
    except RequestValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        )
    job_id = await register(git_url, request.state.agent)
    background_tasks.add_task(post_process, request, job_id)
    build = BuildRead(**dict(create_build(repo, dbsession)._mapping)) # this needs to get called in register
    return {
        "git_repository_url": repo.git_repository_url,
        "build_id": build.build_id,
        "commit_hash": build.commit_hash,
        "build_status": build.build_status,
        "created_at": build.created_at,
    }
