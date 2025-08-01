from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks
from fastapi.exceptions import RequestValidationError

from buildserver.builds.models import BuildCreate, BuildRead
from buildserver.builds.service import validate, register, post_process

router = APIRouter(prefix="/builds")


@router.post("/register", response_model=BuildRead)
async def register_build(repo: BuildCreate, background_tasks: BackgroundTasks, request: Request):
    """
    Registers a new program to be built
    """
    try:
        validate(repo.repository_url)
    except RequestValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        )
    job_id = await register(repo.repository_url, request.state.agent)
    background_tasks.add_task(post_process, request, job_id)
    return {
        "job_id": job_id,
        "repository_url": repo.repository_url,
    }
