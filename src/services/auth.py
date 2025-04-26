"""AuthService Module

This module provides the AuthService class, which handles user authentication, registration, and token management.
It includes methods for creating and validating access and refresh tokens, as well as user authentication and registration.
"""

from datetime import datetime, timedelta, timezone
import json
import secrets

import jwt
import bcrypt
import hashlib
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.exceptions import ConnectionError
from libgravatar import Gravatar

from src.conf.config import settings
from src.entity.models import User
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.utils.hash_password import hash_password

redis_client = redis.from_url(settings.REDIS_URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    """Service for handling authentication and user-related operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the AuthService with a database session.

        Args:
            db (AsyncSession): The database session.
        """
        self.db = db
        self.user_repository = UserRepository(db)
        self.refresh_token_repository = RefreshTokenRepository(db)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify if a plain password matches a hashed password.

        Args:
            plain_password (str): The plain text password.
            hashed_password (str): The hashed password.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    def _hash_token(self, token: str):
        """Hash a token using SHA-256.

        Args:
            token (str): The token to hash.

        Returns:
            str: The hashed token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def authenticate(self, username: str, password: str) -> User:
        """Authenticate a user by username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            User: The authenticated user.

        Raises:
            HTTPException: If authentication fails.
        """
        user = await self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if not user.confirmed:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not confirmed",
            )

        if not self._verify_password(password, user.hash_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        return user

    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user.

        Args:
            user_data (UserCreate): The data of the user to register.

        Returns:
            User: The registered user.

        Raises:
            HTTPException: If the username or email already exists.
        """
        if await self.user_repository.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists"
            )
        if await self.user_repository.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )
        avatar = None
        try:
            g = Gravatar(user_data.email)
            avatar = g.get_image()
        except Exception as e:
            print(f"Error generating Gravatar: {e}")
        hashed_password = hash_password(user_data.password)
        user = await self.user_repository.create_user(
            user_data, hashed_password, avatar
        )
        return user

    def create_access_token(self, username: str) -> str:
        """Create an access token for a user.

        Args:
            username (str): The username of the user.

        Returns:
            str: The generated access token.
        """
        expires_delts = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires = datetime.now(timezone.utc) + expires_delts

        to_encode = {"sub": username, "exp": expires}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def create_refresh_token(
        self, user_id: int, ip_address: str | None, user_agent: str | None
    ) -> str:
        """Create a refresh token for a user.

        Args:
            user_id (int): The ID of the user.
            ip_address (str | None): The IP address of the user.
            user_agent (str | None): The user agent of the user.

        Returns:
            str: The generated refresh token.
        """
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_token_repository.save_token(
            user_id, token_hash, expires_at, ip_address, user_agent
        )
        return token

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Get the current user based on the provided token.

        Args:
            token (str): The access token.

        Returns:
            User: The current user.

        Raises:
            HTTPException: If the token is invalid or revoked.
        """
        try:
            if await redis_client.exists(f"bl:{token}") > 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )
        except ConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection error",
            )

        cache_key = f"user:{token}"
        cached_user = await redis_client.get(cache_key)
        if cached_user:
            user_dict = json.loads(cached_user)
            return User(**user_dict)

        payload = self.decode_and_validate_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user = await self.user_repository.get_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "role": user.role,
        }
        await redis_client.setex(cache_key, 3600, json.dumps(user_dict))

        return user

    def decode_and_validate_access_token(self, token: str) -> dict:
        """Decode and validate an access token.

        Args:
            token (str): The access token to decode.

        Returns:
            dict: The decoded token payload.

        Raises:
            HTTPException: If the token is invalid.
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token wrong"
            )

    async def validate_refresh_token(self, token: str) -> User:
        """Validate a refresh token and retrieve the associated user.

        Args:
            token (str): The refresh token to validate.

        Returns:
            User: The user associated with the refresh token.

        Raises:
            HTTPException: If the refresh token is invalid.
        """
        token_hash = self._hash_token(token)
        current_time = datetime.now(timezone.utc)
        refresh_token = await self.refresh_token_repository.get_active_token(
            token_hash=token_hash, current_time=current_time
        )
        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        user = await self.user_repository.get_by_id(refresh_token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        return user

    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke a refresh token.

        Args:
            token (str): The refresh token to revoke.

        Returns:
            None
        """
        token_hash = self._hash_token(token)
        refresh_token = await self.refresh_token_repository.get_by_token_hash(
            token_hash
        )
        if refresh_token and not refresh_token.revoked_at:
            await self.refresh_token_repository.revoke_token(refresh_token)
        return None

    async def revoke_access_token(self, token: str) -> None:
        """Revoke an access token.

        Args:
            token (str): The access token to revoke.

        Returns:
            None
        """
        payload = self.decode_and_validate_access_token(token)
        exp = payload.get("exp")
        if exp:
            await redis_client.setex(
                f"bl:{token}", int(exp - datetime.now(timezone.utc).timestamp()), "1"
            )
        return None
