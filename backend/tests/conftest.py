import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app as fastapi_app


@pytest.fixture
def app():
    return fastapi_app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac