"""User Service Module

This module provides the UserService class, which contains methods for managing user-related operations such as creating users, retrieving user information, updating user avatars, and handling password changes. It also integrates with Redis for token management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from fastapi import HTTPException, status

from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService
from src.conf.config import settings
from src.utils.hash_password import hash_password

redis_client = redis.from_url(settings.REDIS_URL)


class UserService:
    """Service class for managing user-related operations.

    Attributes:
        db (AsyncSession): The database session for interacting with the database.
        user_repository (UserRepository): Repository for user-related database operations.
        auth_service (AuthService): Service for authentication-related operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data (UserCreate): The data for creating a new user.

        Returns:
            User: The created user object.
        """
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username.

        Args:
            username (str): The username of the user.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email.

        Args:
            email (str): The email of the user.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        user = await self.user_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        """Confirm a user's email.

        Args:
            email (str): The email to confirm.
        """
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        """Update the avatar URL for a user.

        Args:
            email (str): The email of the user.
            url (str): The new avatar URL.

        Returns:
            None
        """
        return await self.user_repository.update_avatar_url(email, url)

    async def change_password(self, token: str, new_password: str) -> None:
        """Change a user's password.

        Args:
            token (str): The reset token.
            new_password (str): The new password to set.

        Raises:
            HTTPException: If the token is invalid or expired, or if the user is not found.
        """
        email = await self.get_email_from_redis(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        new_hashed_password = hash_password(new_password)
        await self.user_repository.change_password(email, new_hashed_password)
        await self.delete_token_from_redis(token)

    async def save_token_to_redis(self, email: str, token: str) -> None:
        """Save a reset token to Redis.

        Args:
            email (str): The email associated with the token.
            token (str): The reset token.
        """
        await redis_client.setex(f"reset_token:{token}", 900, email)

    async def get_email_from_redis(self, token: str) -> str | None:
        """Retrieve an email from Redis using a token.

        Args:
            token (str): The reset token.

        Returns:
            str | None: The email if found, otherwise None.
        """
        email = await redis_client.get(f"reset_token:{token}")
        return email.decode() if email else None

    async def delete_token_from_redis(self, token: str) -> None:
        """Delete a reset token from Redis.

        Args:
            token (str): The reset token to delete.
        """
        await redis_client.delete(f"reset_token:{token}")
