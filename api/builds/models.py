from uuid import UUID
from pydantic import BaseModel


class BuildCreate(BaseModel):
    repository_url: str


class BuildRead(BaseModel):
    job_id: UUID
    repository_url: str
