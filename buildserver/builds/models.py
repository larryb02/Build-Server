from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from buildserver.builder.builder import BuildStatus
from buildserver.database.core import Base


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
    artifact_file: Mapped[bytes] = mapped_column(LargeBinary()) # NOTE: remove this
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(String(40)) # max length of a sha-1 hash
    artifact_repository_id: Mapped[int] = mapped_column(ForeignKey("artifactrepository.artifact_repository_id"))

"""
The following models are 
"""
class BuildRead(BaseModel):
    build_id: int
    # job_id: Optional[UUID]
    git_repository_url: str
    commit_hash: Optional[str]
    build_status: BuildStatus | Status | str
    created_at: datetime

class BuildCreate(BaseModel):
    git_repository_url: str

class Build(Base):
    __tablename__ = "build"
    build_id: Mapped[int] = mapped_column(primary_key=True)
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=True) # add this after successful build
    build_status: Mapped[str] = mapped_column(Enum(BuildStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())