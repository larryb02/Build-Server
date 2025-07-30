from fastapi import APIRouter, HTTPException, status
from fastapi.exceptions import RequestValidationError
from api.repository.models import RepositoryCreate, RepositoryRead
from api.database.core import DbSession
from api.repository.service import create, validate

router = APIRouter(prefix="/repository")


@router.post("", response_model=RepositoryRead)
def register_repo(repo: RepositoryCreate, db_session: DbSession):
    try:
        validate(repo.repository_url)
    except RequestValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"msg": str(e)}],
        )
    try:
        registered_repo = dict(create(repo, db_session)._mapping)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"msg": "Internal Server Error"}],
        )
    return {
        "id": registered_repo["repository_id"],
        "repository_url": registered_repo["repository_url"],
    }
