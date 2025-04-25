"""
Database session management for the application.

This module provides utilities for managing database sessions using SQLAlchemy.
It includes a `DatabaseSessionManager` class for creating and managing
asynchronous database sessions and a dependency function `get_db` for FastAPI.

Classes:
    DatabaseSessionManager: Manages the lifecycle of database sessions.

Functions:
    get_db: Provides a database session for FastAPI dependency injection.
"""

import contextlib
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseSessionManager:
    """Manages the lifecycle of asynchronous database sessions.

    This class is responsible for creating and managing database sessions
    using SQLAlchemy's asynchronous engine and session maker.

    Attributes:
        _engine (AsyncEngine): The SQLAlchemy asynchronous engine.
        _session_maker (async_sessionmaker): The session maker for creating sessions.
    """

    def __init__(self, url: str):
        """Initializes the DatabaseSessionManager with the given database URL.

        Args:
            url (str): The database connection URL.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """Provides an asynchronous context manager for database sessions.

        Yields:
            AsyncSession: A SQLAlchemy asynchronous session.

        Raises:
            Exception: If the session maker is not initialized.
            SQLAlchemyError: If a database error occurs during the session.
            Exception: If an unexpected error occurs during the session.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error("Database error: %s", e)
            await session.rollback()
            raise
        except Exception as e:
            logger.error("Unexpected error: %s", e, exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)
"""
Instance of DatabaseSessionManager.

This instance is used to manage database sessions throughout the application.
"""


async def get_db():
    """Provides a database session for FastAPI dependency injection.

    This function is used as a dependency in FastAPI routes to provide
    a database session for handling database operations.

    Yields:
        AsyncSession: A SQLAlchemy asynchronous session.
    """
    async with sessionmanager.session() as session:
        yield session
