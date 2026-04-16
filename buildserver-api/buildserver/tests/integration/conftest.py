"""Fixtures for integration tests"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from testcontainers.postgres import PostgresContainer

import buildserver.database.models  # noqa: F401 — registers all ORM models on Base
from buildserver.database.core import Base

# from ...config import (
#     DATABASE_USER,
#     DATABASE_PASSWORD,
#     DATABASE_HOSTNAME,
#     DATABASE_PORT,
# )

# TEST_DATABASE_URI = (
#     f"postgresql+psycopg2://{DATABASE_USER}:{DATABASE_PASSWORD}"
#     f"@{DATABASE_HOSTNAME}:{DATABASE_PORT}/test"
# )


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer() as postgres:
        yield postgres
    # os.environ["DB_CONN"] = postgres.get_connection_url()
    # os.environ["DB_HOST"] = postgres.get_container_host_ip()
    # os.environ["DB_PORT"] = postgres.get_exposed_port(5432) # type: ignore
    # os.environ["DB_USERNAME"] = postgres.username
    # os.environ["DB_PASSWORD"] = postgres.password
    # os.environ["DB_NAME"] = postgres.dbname


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Create SQLAlchemy engine from container connection"""
    engine = create_engine(postgres_container.get_connection_url())
    return engine


@pytest.fixture(scope="function")
def dbsession(db_engine):
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=db_engine)
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
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
    Base.metadata.drop_all(bind=db_engine)
