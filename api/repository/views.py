from fastapi import APIRouter, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from api.repository.models import ArtifactRepositoryCreate, ArtifactRepositoryRead
from api.database.core import DbSession
from api.repository.service import create_repository

router = APIRouter(prefix="/artifacts")


@router.post("/repository", response_model=ArtifactRepositoryRead)
def create_artifact_repository(
    repo: ArtifactRepositoryCreate, db_session: DbSession, request: Request
):
    logger = request.state.logger
    try:
        record = dict(create_repository(repo, db_session)._mapping)
    except Exception as e:
        logger.error("Failed to create entry: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"msg": "Internal Server Error"}],
        )
    return {
        "id": record["artifact_repository_id"],
        "repository_name": record["artifact_repository_name"],
        "artifacts": [] # there will be no artifacts because repository was just created
    }


