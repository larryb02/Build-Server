from sqlalchemy import insert

from buildserver.repository.models import (
    ArtifactRepository,
    ArtifactRepositoryCreate,
)
from buildserver.database.core import DbSession


def create_repository(repo: ArtifactRepositoryCreate, dbsession: DbSession):
    stmt = (
        insert(ArtifactRepository)
        .values(artifact_repository_name=repo.repository_name)
        .returning(
            ArtifactRepository.artifact_repository_id,
            ArtifactRepository.artifact_repository_name,
        )
    )
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record
