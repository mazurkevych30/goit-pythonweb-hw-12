"""
conftest.py

This module contains pytest fixtures for setting up and managing the test environment.
It includes database initialization, a FastAPI test client, and utilities for generating
authentication tokens for testing purposes.
"""

import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.entity.models import Base, User, UserRole
from src.database.db import get_db
from src.services.auth import AuthService
from src.utils.hash_password import hash_password


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "Vladyslav",
    "email": "vladyslav@example.com",
    "password": "123456",
    "role": "ADMIN",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    """
    Initializes the database models for testing.

    This fixture sets up the database by dropping all existing tables and
    recreating them. It also adds a test user to the database.

    Yields:
        None
    """

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_pass = hash_password(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                hash_password=hash_pass,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=UserRole.ADMIN,
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    """
    Provides a FastAPI test client with an overridden database dependency.

    This fixture overrides the `get_db` dependency of the FastAPI app to use
    the testing database session.

    Yields:
        TestClient: A test client for the FastAPI app.
    """

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise err

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token():
    """
    Generates an access token for the test user.

    This fixture uses the `AuthService` to create an access token for the
    predefined test user.

    Returns:
        str: A valid access token for the test user.
    """
    async with TestingSessionLocal() as session:
        auth_service = AuthService(session)
        token = auth_service.create_access_token(test_user["username"])
    return token
