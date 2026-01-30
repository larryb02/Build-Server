"""Database engine, session, and base model configuration"""

from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session, Session
from fastapi import Depends
from buildserver.config import DATABASE_URI

engine = create_engine(DATABASE_URI)
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)


def get_session():
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


def create_session() -> scoped_session[Session]:
    return SessionLocal()


DbSession = Annotated[scoped_session, Depends(get_session)]


class Base(DeclarativeBase):
    pass
