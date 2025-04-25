"""
Repository for refresh token-related database operations.

This module defines the `RefreshTokenRepository` class, which provides methods
for managing refresh tokens, including saving, retrieving, and revoking tokens.

Classes:
    RefreshTokenRepository: A repository for managing refresh token-related database operations.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repositories.base import BaseRepository

logger = logging.getLogger("uvicorn.error")


class RefreshTokenRepository(BaseRepository):
    """A repository for managing refresh token-related database operations.

    This class provides methods for saving, retrieving, and revoking refresh tokens.
    """

    def __init__(self, session: AsyncSession):
        """Initializes the RefreshTokenRepository with a database session.

        Args:
            session (AsyncSession): The database session.
        """
        super().__init__(session, RefreshToken)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Retrieves a refresh token by its token hash.

        Args:
            token_hash (str): The hash of the refresh token to retrieve.

        Returns:
            RefreshToken | None: The refresh token if found, or None if not found.
        """
        stmt = select(self.model).where(RefreshToken.token_hash == token_hash)
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def get_active_token(
        self, token_hash: str, current_time: datetime
    ) -> RefreshToken | None:
        """Retrieves an active refresh token by its token hash.

        Args:
            token_hash (str): The hash of the refresh token to retrieve.
            current_time (datetime): The current time to check token expiration.

        Returns:
            RefreshToken | None: The active refresh token if found, or None if not found.
        """
        stmt = select(self.model).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > current_time,
            RefreshToken.revoked_at.is_(None),
        )
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def save_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> RefreshToken:
        """Saves a new refresh token in the database.

        Args:
            user_id (int): The ID of the user associated with the token.
            token_hash (str): The hash of the refresh token.
            expires_at (datetime): The expiration time of the token.
            ip_address (str): The IP address from which the token was issued.
            user_agent (str): The user agent string of the client.

        Returns:
            RefreshToken: The created refresh token instance.
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(refresh_token)

    async def revoke_token(self, refresh_token: RefreshToken) -> None:
        """Revokes a refresh token by setting its revoked_at timestamp.

        Args:
            refresh_token (RefreshToken): The refresh token to revoke.

        Returns:
            None
        """
        refresh_token.revoked_at = datetime.now()
        await self.db.commit()
