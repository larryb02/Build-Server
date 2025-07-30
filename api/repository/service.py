from uuid import UUID
from api.repository.models import Repository, RepositoryCreate
from fastapi.exceptions import RequestValidationError
from sqlalchemy import insert


def validate(repo_url):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


def create(repo: RepositoryCreate, dbsession):
    stmt = (
        insert(Repository)
        .values(repository_url=repo.repository_url)
        .returning(Repository.repository_id, Repository.repository_url)
    )
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record

async def register(repo: str, agent) -> UUID:
    job_id = await agent.add_job(repo)
    return job_id