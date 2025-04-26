"""
Unit tests for the UserRepository class.

This module contains tests for the following methods of the UserRepository:
- get_by_username: Retrieves a user by their username.
- get_user_by_email: Retrieves a user by their email.
- create_user: Creates a new user in the database.
- confirmed_email: Confirms a user's email.
- update_avatar_url: Updates the avatar URL of a user.
- change_password: Changes the password of a user.
"""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.entity.models import User


@pytest.fixture
def mock_session():
    """Creates a mock AsyncSession for database interactions.

    Returns:
        AsyncMock: A mock object simulating an AsyncSession.
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    """Creates an instance of UserRepository with a mock session.

    Args:
        mock_session (AsyncMock): The mock database session.

    Returns:
        UserRepository: An instance of UserRepository.
    """
    return UserRepository(mock_session)


@pytest.fixture
def test_user():
    """Creates a test user object.

    Returns:
        User: A mock user object.
    """
    return User(id=1, username="testuser", email="test@example.com")


@pytest.mark.asyncio
async def test_get_by_username(user_repository, mock_session, test_user):
    """Tests the get_by_username method.

    Verifies that the method retrieves the correct user by username
    and that the database query is executed once.

    Args:
        user_repository (UserRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        test_user (User): The test user object.
    """
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_by_username("testuser")

    assert result == test_user
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, test_user):
    """Tests the get_user_by_email method.

    Verifies that the method retrieves the correct user by email
    and that the database query is executed once.

    Args:
        user_repository (UserRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        test_user (User): The test user object.
    """
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_email("test@example.com")

    assert result == test_user
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user(user_repository):
    """Tests the create_user method.

    Verifies that the method creates a new user and returns the created user.

    Args:
        user_repository (UserRepository): The repository instance.
    """
    user_data = UserCreate(
        username="newuser", email="new@example.com", password="123456"
    )
    hash_password = "hashpassword"
    avatar = "avatar_url"

    mock_user = User(
        username="newuser",
        email="ew@example.com",
        hash_password="hashpassword",
        avatar="avatar_url",
    )

    user_repository.create = AsyncMock(return_value=mock_user)

    result = await user_repository.create_user(user_data, hash_password, avatar)

    assert result == mock_user
    user_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session, test_user):
    """Tests the confirmed_email method.

    Verifies that the user's email is marked as confirmed and that
    the database commit is executed.

    Args:
        user_repository (UserRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        test_user (User): The test user object.
    """
    user_repository.get_user_by_email = AsyncMock(return_value=test_user)

    await user_repository.confirmed_email(test_user.email)

    assert test_user.confirmed is True
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session, test_user):
    """Tests the update_avatar_url method.

    Verifies that the user's avatar URL is updated and that
    the database commit and refresh are executed.

    Args:
        user_repository (UserRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        test_user (User): The test user object.
    """
    new_avatar_url = "new_avatar_url"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    await user_repository.update_avatar_url(test_user.email, new_avatar_url)

    assert test_user.avatar == new_avatar_url
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(test_user)


@pytest.mark.asyncio
async def test_change_password(user_repository, mock_session, test_user):
    """Tests the change_password method.

    Verifies that the user's password is updated and that
    the database commit is executed.

    Args:
        user_repository (UserRepository): The repository instance.
        mock_session (AsyncMock): The mock database session.
        test_user (User): The test user object.
    """
    new_hashed_password = "new_hash_password"
    user_repository.get_user_by_email = AsyncMock(return_value=test_user)

    await user_repository.change_password(test_user.email, new_hashed_password)

    assert test_user.hash_password == new_hashed_password
    mock_session.commit.assert_awaited_once()
