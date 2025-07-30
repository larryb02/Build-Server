from fastapi import APIRouter, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError

from api.builds.models import BuildCreate, BuildRead
from api.builds.service import validate, register

router = APIRouter(prefix="/builds")


@router.post("/register", response_model=BuildRead)
async def register_build(repo: BuildCreate, request: Request):
    """
    Registers a new build to be processed by the Builder
    """
    try:
        validate(repo.repository_url)
    except RequestValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        )
    job_id = await register(repo.repository_url, request.state.agent)
    return {
        "job_id": job_id,
        "repository_url": repo.repository_url,
    }
