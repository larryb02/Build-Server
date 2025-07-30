from fastapi.exceptions import RequestValidationError
from uuid import UUID


def validate(repo_url):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


async def register(repo: str, agent) -> UUID:
    job_id = await agent.add_job(repo)
    return job_id
