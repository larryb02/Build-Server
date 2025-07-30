from fastapi import APIRouter, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from api.repository.models import RepositoryCreate, RepositoryRead
from api.database.core import DbSession
from api.repository.service import create, validate, register

router = APIRouter(prefix="/repository")


@router.post("", response_model=RepositoryRead)
async def register_repo(repo: RepositoryCreate, db_session: DbSession, request: Request):
    try:
        validate(repo.repository_url)
    except RequestValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        )
    try:
        # registered_repo = dict(create(repo, db_session)._mapping) wont write to db until i actually need data to persist
        registered_repo = {"repository_id": 0, "repository_url": "/hello.git"} # filler values until i write to db again
        job_id = await register(repo.repository_url, request.state.agent)
    except Exception as e:
        request.state.logger.error("Failed to register repo: ", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"msg": "Internal Server Error"}],
        )
    return {
        "id": registered_repo["repository_id"],
        "repository_url": registered_repo["repository_url"],
    }
