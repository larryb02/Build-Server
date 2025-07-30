from pydantic import BaseModel
from api.database.core import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class RepositoryCreate(BaseModel):
    repository_url: str


class RepositoryRead(BaseModel):
    id: int
    repository_url: str


class Repository(Base):
    __tablename__ = "repository"
    repository_id: Mapped[int] = mapped_column(primary_key=True)
    repository_url: Mapped[str] = mapped_column(String(255), unique=True)
