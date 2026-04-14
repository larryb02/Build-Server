"""SQLAlchemy and Pydantic models for Pipeline, PipelineJob, and Artifact"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ...database.core import Base


class PipelineStatus(str, PyEnum):
    """Execution status shared across Pipeline and PipelineJob."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class Pipeline(Base):
    __tablename__ = "pipeline"

    pipeline_id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.project_id"))
    branch: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(Enum(PipelineStatus, name="pipelinestatus"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PipelineJob(Base):
    __tablename__ = "pipeline_job"

    pipeline_job_id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipeline.pipeline_id"))
    name: Mapped[str] = mapped_column(String(255))
    commands: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        Enum(PipelineStatus, name="pipelinestatus", create_constraint=False)
    )
    runner_id: Mapped[int] = mapped_column(
        ForeignKey("runner.runner_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Artifact(Base):
    __tablename__ = "artifact"

    artifact_id: Mapped[int] = mapped_column(primary_key=True)
    artifact_file_name: Mapped[str] = mapped_column(String(255))
    artifact_path: Mapped[str] = mapped_column(String(255))
    git_repository_url: Mapped[str] = mapped_column(String(255))
    commit_hash: Mapped[str] = mapped_column(String(40))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PipelineJobRead(BaseModel):
    """PipelineJob payload dispatched to a runner."""

    pipeline_job_id: int
    pipeline_id: int
    name: str
    commands: list[str]
    git_repository_url: str  # denormalized from project for runner convenience
    commit_hash: str  # denormalized from pipeline
    status: PipelineStatus
    created_at: datetime


class PipelineJobStatusUpdate(BaseModel):
    status: PipelineStatus


class PipelineJobResponse(BaseModel):
    job: Optional[PipelineJobRead]


class PipelineRead(BaseModel):
    pipeline_id: int
    project_id: int
    branch: str
    commit_hash: str
    status: PipelineStatus
    created_at: datetime


class PipelineJobSummary(BaseModel):
    pipeline_job_id: int
    name: str
    status: PipelineStatus
    created_at: datetime


class PipelineDetail(BaseModel):
    pipeline_id: int
    project_id: int
    project_name: str
    branch: str
    commit_hash: str
    status: PipelineStatus
    created_at: datetime
    jobs: list[PipelineJobSummary]


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
