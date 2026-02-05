"""
Type definitions for Job related objects
"""

from enum import Enum
import uuid
from pydantic import BaseModel


class JobStatus(str, Enum):
    """Represents the current state of a job in the build pipeline."""

    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CREATED = "CREATED"


class JobStatusUpdate(BaseModel):
    """Request body for updating a job's current status."""

    job_status: JobStatus


class Job(BaseModel):
    """
    A job is what gets executed
    """

    job_id: uuid.UUID
    git_repository_url: str
    job_status: JobStatus
