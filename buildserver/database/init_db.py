"""Initialize database schema"""

from sqlalchemy.orm import Session

from buildserver.database.core import Base, engine
import buildserver.builds.models
import buildserver.repository.models

with Session(engine) as session:
    session.begin()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
