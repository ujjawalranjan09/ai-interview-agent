"""Test fixtures — async test client, test database, auth helpers."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db
from app.core.rate_limit import disable_rate_limit
from app.models import *  # noqa

disable_rate_limit()

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepass123",
            "full_name": "Test User",
            "role": "interviewer",
        },
    )
    assert resp.status_code == 201
    tokens = resp.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, db: AsyncSession) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "adminpass123",
            "full_name": "Admin User",
            "role": "interviewer",
        },
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()

    from sqlalchemy import select
    from app.models.user import User
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    user = result.scalar_one()
    user.role = "admin"
    await db.commit()

    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture
async def candidate_fixture(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/api/v1/candidates",
        json={"name": "Jane Doe", "email": "jane@example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def interview_fixture(client: AsyncClient, auth_headers: dict, candidate_fixture: dict) -> dict:
    resp = await client.post(
        "/api/v1/interviews",
        json={
            "candidate_id": candidate_fixture["id"],
            "question_count": 3,
            "difficulty_level": 2,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()
