from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from api.database.core import Base

class BuildCreate(BaseModel):
    repository_url: str


class BuildRead(BaseModel):
    job_id: UUID
    repository_url: str

class ArtifactRead(BaseModel):
    git_repository_url: str
    commit_hash: str
    artifact_file_name: str
    artifact_file: bytes
    artifact_repository_name: str


class ArtifactCreate(BaseModel):
    git_repository_url: str
    artifact_file_name: str
    artifact_file_contents: bytes
    commit_hash: str
    artifact_repository_id: int

class Artifact(Base):
    __tablename__ = "artifact"
    artifact_id: Mapped[int] = mapped_column(primary_key=True)
    artifact_name: Mapped[str] = mapped_column(String(255))
    artifact_file: Mapped[bytes] = mapped_column(LargeBinary())
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(String(40)) # max length of a sha-1 hash
    artifact_repository_id: Mapped[int] = mapped_column(ForeignKey("artifactrepository.artifact_repository_id"))