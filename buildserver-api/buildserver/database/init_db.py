"""Initialize database schema"""

from sqlalchemy.orm import Session

from buildserver.database.core import Base, engine
import buildserver.api.jobs.models  # noqa: F401

with Session(engine) as session:
    session.begin()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
