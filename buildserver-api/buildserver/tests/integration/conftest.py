"""Fixtures for integration tests"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from buildserver.api.runners.models import Base
from buildserver.config import (
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOSTNAME,
    DATABASE_PORT,
)

TEST_DATABASE_URI = (
    f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOSTNAME}:{DATABASE_PORT}/test"
)


@pytest.fixture
def dbsession():
    """Create a fresh database session for each test."""
    engine = create_engine(TEST_DATABASE_URI)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    SessionLocal = scoped_session(session_factory)
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    Base.metadata.drop_all(bind=engine)
