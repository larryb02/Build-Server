"""Pydantic and SQLAlchemy models for projects"""

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ...database.core import Base


class Project(Base):
    __tablename__ = "project"

    project_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    git_repository_url: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ProjectCreate(BaseModel):
    name: str
    git_repository_url: str


class ProjectRead(BaseModel):
    project_id: int
    name: str
    git_repository_url: str
    created_at: datetime


class TriggerRequest(BaseModel):
    branch: str = "main"
