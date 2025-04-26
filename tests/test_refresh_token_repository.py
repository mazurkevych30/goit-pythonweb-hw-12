"""
Unit tests for the RefreshTokenRepository class.

This module contains unit tests for the following methods of the RefreshTokenRepository:
- get_by_token_hash: Retrieves a refresh token by its token hash.
- get_active_token: Retrieves an active refresh token by its token hash.
- save_token: Saves a new refresh token in the database.
- revoke_token: Revokes a refresh token by setting its revoked_at timestamp.

Fixtures:
    mock_session: Creates a mock AsyncSession for database interactions.
    refresh_token_repository: Creates an instance of RefreshTokenRepository with a mock session.
"""

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.fixture
def mock_session():
    """Creates a mock AsyncSession for database interactions.

    Returns:
        AsyncMock: A mock object simulating an AsyncSession.
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def refresh_token_repository(mock_session: AsyncMock):
    """Creates an instance of RefreshTokenRepository with a mock session.

    Args:
        mock_session (AsyncMock): The mock database session.

    Returns:
        RefreshTokenRepository: An instance of RefreshTokenRepository.
    """
    return RefreshTokenRepository(mock_session)


@pytest.mark.asyncio
async def test_get_by_token_hash(
    refresh_token_repository: RefreshTokenRepository, mock_session: AsyncMock
):
    """Tests the get_by_token_hash method.

    Verifies that the method retrieves the correct refresh token by its token hash
    and that the database query is executed once.

    Args:
        refresh_token_repository (RefreshTokenRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
    """
    token_hash = "test_token_hash"
    mock_token = RefreshToken(token_hash=token_hash)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_token
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_by_token_hash(token_hash)

    assert result == mock_token
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_active_token(
    refresh_token_repository: RefreshTokenRepository, mock_session: AsyncMock
):
    """Tests the get_active_token method.

    Verifies that the method retrieves the correct active refresh token by its token hash
    and that the database query is executed once.

    Args:
        refresh_token_repository (RefreshTokenRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
    """
    token_hash = "test_token_hash"
    current_time = datetime.now(timezone.utc)
    expires_at = current_time + timedelta(days=1)
    mock_token = RefreshToken(
        token_hash=token_hash, expires_at=expires_at, revoked_at=None
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_token
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_active_token(token_hash, current_time)

    assert result == mock_token
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_token(
    refresh_token_repository: RefreshTokenRepository, mock_session: AsyncMock
):
    """Tests the save_token method.

    Verifies that the method saves a new refresh token in the database
    and that the create method is called once.

    Args:
        refresh_token_repository (RefreshTokenRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
    """
    user_id = 1
    token_hash = "test_token_hash"
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    ip_address = "127.0.0.1"
    user_agent = "TestUserAgent"
    mock_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    refresh_token_repository.create = AsyncMock(return_value=mock_token)

    result = await refresh_token_repository.save_token(
        user_id, token_hash, expires_at, ip_address, user_agent
    )

    assert result == mock_token
    refresh_token_repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_token(
    refresh_token_repository: RefreshTokenRepository, mock_session: AsyncMock
):
    """Tests the revoke_token method.

    Verifies that the method revokes a refresh token by setting its revoked_at timestamp
    and that the commit method is called once.

    Args:
        refresh_token_repository (RefreshTokenRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
    """
    mock_token = RefreshToken(token_hash="test_token_hash")

    await refresh_token_repository.revoke_token(mock_token)

    assert mock_token.revoked_at is not None
    mock_session.commit.assert_awaited_once()
