# from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from buildserver.database.core import Base


class Runner(Base):
    __tablename__ = "runner"
    runner_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    runner_token_hash: Mapped[str] = mapped_column(String(40))
