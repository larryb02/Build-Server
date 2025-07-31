from api.repository.models import (
    ArtifactRepository,
    ArtifactRepositoryCreate,
)
from sqlalchemy import insert


def create_repository(repo: ArtifactRepositoryCreate, dbsession):
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
