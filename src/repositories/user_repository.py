"""
Repository for user-related database operations.

This module defines the `UserRepository` class, which provides methods
for performing CRUD operations and other user-specific database interactions.

Classes:
    UserRepository: A repository for managing user-related database operations.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class UserRepository(BaseRepository):
    """A repository for managing user-related database operations.

    This class extends the `BaseRepository` and provides additional methods
    specific to user-related operations, such as retrieving users by username
    or email, creating users, confirming email, updating avatars, and changing passwords.
    """

    def __init__(self, session: AsyncSession):
        """Initializes the UserRepository with a database session.

        Args:
            session (AsyncSession): The database session.
        """
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        """Retrieves a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user with the specified username, or None if not found.
        """
        stmt = select(self.model).where(self.model.username == username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieves a user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user with the specified email, or None if not found.
        """
        stmt = select(self.model).where(self.model.email == email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, user_data: UserCreate, hashed_password: str, avatar: str
    ) -> User:
        """Creates a new user in the database.

        Args:
            user_data (UserCreate): The data for the new user.
            hashed_password (str): The hashed password for the user.
            avatar (str): The URL of the user's avatar.

        Returns:
            User: The created user instance.
        """
        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hash_password=hashed_password,
            avatar=avatar,
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        """Marks a user's email as confirmed.

        Args:
            email (str): The email address of the user to confirm.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """Updates the avatar URL for a user.

        Args:
            email (str): The email address of the user.
            url (str): The new avatar URL.

        Returns:
            User: The updated user instance.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, email: str, new_hashed_password: str) -> None:
        """Changes the password for a user.

        Args:
            email (str): The email address of the user.
            new_hashed_password (str): The new hashed password.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.hash_password = new_hashed_password
        await self.db.commit()
