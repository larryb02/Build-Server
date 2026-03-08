from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Enum
from protos.registry_pb2 import RunnerHealth

from buildserver.database.core import Base


class RegistrationTokenResponse(BaseModel):
    token: str
    created_at: datetime
    expires_at: datetime


class Runner(Base):
    __tablename__ = "runner"
    runner_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    runner_token_hash: Mapped[str] = mapped_column(String(64))
    health: Mapped[RunnerHealth] = mapped_column(
        Enum(RunnerHealth)
    )  # maps to RunnerStatus enum
