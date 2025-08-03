from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from buildserver.builder.builder import BuildStatus
from buildserver.database.core import Base


class ArtifactRead(BaseModel):
    git_repository_url: str
    commit_hash: str
    artifact_file_name: str
    artifact_path: str


class ArtifactCreate(BaseModel):
    git_repository_url: str
    artifact_file_name: str
    artifact_path: str
    commit_hash: str


class Artifact(Base):
    __tablename__ = "artifact"
    artifact_id: Mapped[int] = mapped_column(primary_key=True)
    artifact_file_name: Mapped[str] = mapped_column(String(255))
    artifact_path: Mapped[str] = mapped_column(String(255))
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(String(40))  # max length of a sha-1 hash


class BuildRead(BaseModel):
    build_id: int
    # job_id: Optional[UUID]
    git_repository_url: str
    commit_hash: Optional[str]
    build_status: BuildStatus
    created_at: datetime


class BuildCreate(BaseModel):
    git_repository_url: str


class Build(Base):
    __tablename__ = "build"
    build_id: Mapped[int] = mapped_column(primary_key=True)
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(
        String(40), nullable=True
    )  # add this after successful build
    build_status: Mapped[str] = mapped_column(Enum(BuildStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
