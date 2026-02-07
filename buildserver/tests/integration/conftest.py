"""Fixtures for integration tests"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from buildserver.api.jobs.models import Base
from buildserver.config import Config

config = Config()


@pytest.fixture
def dbsession():
    """Create a fresh database session for each test."""
    engine = create_engine(config.DATABASE_URI)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)
