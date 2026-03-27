from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime

from buildserver.database.core import Base


class HeartbeatRequest(BaseModel):
    token: str


class RunnerHealth(IntEnum):
    OFFLINE = 0
    UNHEALTHY = 1
    HEALTHY = 2


class RegisterRequest(BaseModel):
    token: str
    name: str


class GenerateTokenResponse(BaseModel):
    token: str
    created_at: datetime
    expires_at: datetime


class RunnerRead(BaseModel):
    model_config = {"from_attributes": True}

    runner_id: int
    name: str
    health: RunnerHealth
    last_seen: datetime


class PendingTokens(Base):
    __tablename__ = "pending_token"
    token_id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Runner(Base):
    __tablename__ = "runner"
    runner_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    runner_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    health: Mapped[int] = mapped_column(Integer, default=RunnerHealth.OFFLINE)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
