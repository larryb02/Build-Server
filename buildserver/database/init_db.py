from buildserver.database.core import Base, engine
from buildserver.builds.models import Artifact
from buildserver.repository.models import ArtifactRepository
from sqlalchemy.orm import Session

with Session(engine) as session:
    session.begin()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
