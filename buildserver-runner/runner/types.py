"""Type definitions for the runner package"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PipelineJob(BaseModel):
    """A pipeline job dispatched to this runner."""

    pipeline_job_id: int
    pipeline_id: int
    name: str
    commands: list[str]
    git_repository_url: str
    commit_hash: str
    status: JobStatus
    created_at: datetime
