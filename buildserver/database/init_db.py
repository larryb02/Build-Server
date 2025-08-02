from buildserver.database.core import Base, engine
import buildserver.builds.models
import buildserver.repository.models
from sqlalchemy.orm import Session

with Session(engine) as session:
    session.begin()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
