"""Fixtures for end-to-end tests"""

import pytest
import pytest_asyncio
import httpx
from asgi_lifespan import LifespanManager

from buildserver.database.core import engine, Base
from buildserver.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    """Async HTTP client with lifespan support."""
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as ac:
            yield ac
