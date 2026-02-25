"""Type definitions for the agent package"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    """Represents the current state of a job in the build pipeline."""

    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    # CREATED = "CREATED"


class Job(BaseModel):
    """A job consumed from the build queue."""

    job_id: int
    git_repository_url: str
    commit_hash: Optional[str]
    job_status: JobStatus
    created_at: datetime
    script: str
