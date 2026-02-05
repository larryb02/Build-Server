"""Pydantic and SQLAlchemy models for jobs and artifacts"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from buildserver.models.jobs import JobStatus
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


class JobRead(BaseModel):
    """Response model representing a job record."""

    job_id: int
    git_repository_url: str
    commit_hash: Optional[str]
    job_status: JobStatus
    created_at: datetime


class JobCreate(BaseModel):
    """Request model for submitting a new job."""

    git_repository_url: str


class Job(Base):
    """
    Database model for Job
    """

    __tablename__ = "job"
    job_id: Mapped[int] = mapped_column(primary_key=True)
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(
        String(40), nullable=True
    )  # add this after successful build
    job_status: Mapped[str] = mapped_column(Enum(JobStatus, name="jobstatus"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
