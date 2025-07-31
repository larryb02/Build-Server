from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database.core import Base

class ArtifactRead(BaseModel):
    git_repository_url: str
    commit_hash: str
    artifact_file_name: str
    artifact_file: bytes
    artifact_repository_name: str

class ArtifactRepositoryCreate(BaseModel):
    repository_name: str = "Default Artifact Repository"


class ArtifactRepositoryRead(BaseModel):
    id: int
    repository_name: str
    artifacts: list[ArtifactRead]


class ArtifactRepository(Base):
    __tablename__ = "artifactrepository"
    artifact_repository_id: Mapped[int] = mapped_column(primary_key=True)
    artifact_repository_name: Mapped[str] = mapped_column(
        String(50), default="Default Artifact Repository"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="artifact_repository")