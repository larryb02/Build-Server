from typing import Annotated
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from fastapi import Depends
from api.config import DATABASE_URI


engine = create_engine(DATABASE_URI)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def get_session():
    with Session() as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


DbSession = Annotated[scoped_session, Depends(get_session)]


class Base(DeclarativeBase):
    pass
