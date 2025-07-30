from api.database.core import Base, engine
from api.repository.models import Repository
from sqlalchemy.orm import Session

with Session(engine) as session:
    session.begin()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()
