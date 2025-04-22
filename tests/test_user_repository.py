# from unittest.mock import AsyncMock, Mock, MagicMock

# from sqlalchemy.ext.asyncio import AsyncSession
# import pytest

# from src.repositories.user_repository import UserRepository
# from src.schemas.user import UserCreate
# from src.entity.models import User


# @pytest.fixture
# def mock_session():
#     session = AsyncMock(spec=AsyncSession)
#     session.execute = AsyncMock()
#     session.commit = AsyncMock()
#     session.refresh = AsyncMock()
#     session.add = Mock()
#     return session


# @pytest.fixture
# def user_repository(mock_session):
#     return UserRepository(mock_session)


# @pytest.fixture
# def test_user():
#     return User(id=1, username="testuser", email="test@example.com")


# @pytest.mark.asyncio
# async def test_get_by_username(user_repository, mock_session, test_user):
#     """
#     Test the get_by_username method of UserRepository.
#     Ensures it retrieves the correct user by username.
#     """
#     # Mock the result of session.execute
#     mock_result = AsyncMock()
#     mock_result.scalar_one_or_none.return_value = test_user
#     mock_session.execute.return_value = mock_result

#     # Call the method
#     result = await user_repository.get_by_username("testuser")

#     # Assertions
#     assert result == test_user
#     mock_session.execute.assert_called_once()


# # @pytest.mark.asyncio
# # async def test_get_user_by_email(user_repository, mock_session, sample_user):
# #     mock_session.execute = AsyncMock()
# #     mock_session.execute.return_value.scalar_one_or_none = AsyncMock(
# #         return_value=sample_user
# #     )

# #     result = await user_repository.get_user_by_email("test@example.com")

# #     assert result == sample_user
# #     mock_session.execute.assert_called_once()


# # @pytest.mark.asyncio
# # async def test_create_user(user_repository, mock_session):
# #     user_data = UserCreate(
# #         username="newuser", email="new@example.com", password="123456"
# #     )
# #     hashed_password = "hashedpassword"
# #     avatar = "avatar_url"

# #     mock_session.add = MagicMock()
# #     mock_session.commit = AsyncMock()

# #     result = await user_repository.create_user(user_data, hashed_password, avatar)

# #     assert result.username == user_data.username
# #     assert result.email == user_data.email
# #     assert result.hash_password == hashed_password
# #     assert result.avatar == avatar
# #     mock_session.add.assert_called_once()
# #     mock_session.commit.assert_called_once()


# # @pytest.mark.asyncio
# # async def test_confirmed_email(user_repository, mock_session, sample_user):
# #     mock_session.execute = AsyncMock()
# #     mock_session.execute.return_value.scalar_one_or_none = AsyncMock(
# #         return_value=sample_user
# #     )
# #     mock_session.commit = AsyncMock()

# #     await user_repository.confirmed_email("test@example.com")

# #     assert sample_user.confirmed is True
# #     mock_session.commit.assert_called_once()


# # @pytest.mark.asyncio
# # async def test_update_avatar_url(user_repository, mock_session, sample_user):
# #     mock_session.execute = AsyncMock()
# #     mock_session.execute.return_value.scalar_one_or_none = AsyncMock(
# #         return_value=sample_user
# #     )
# #     mock_session.commit = AsyncMock()
# #     mock_session.refresh = AsyncMock()

# #     updated_user = await user_repository.update_avatar_url(
# #         "test@example.com", "new_avatar_url"
# #     )

# #     assert updated_user.avatar == "new_avatar_url"
# #     mock_session.commit.assert_called_once()
# #     mock_session.refresh.assert_called_once_with(sample_user)
