"""Database engine, session, and base model configuration"""

from contextlib import contextmanager
from typing import Annotated, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session, Session
from sqlalchemy_utils import database_exists, create_database
from fastapi import Depends
from ..config import DATABASE_URI

engine = create_engine(
    DATABASE_URI,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
)
session_factory = sessionmaker(bind=engine, expire_on_commit=False)
SessionLocal = scoped_session(session_factory)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


session_context = contextmanager(get_session)
DbSession = Annotated[Session, Depends(get_session)]


class Base(DeclarativeBase):
    pass


def init_db():
    if not database_exists(engine.url):
        create_database(engine.url)
    """Create all database tables."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
