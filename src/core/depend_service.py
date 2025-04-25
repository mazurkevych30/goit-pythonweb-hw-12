"""
Dependency injection services for FastAPI.

This module provides dependency functions for injecting services and
retrieving the current user or admin user. These dependencies are used
throughout the application to manage authentication, authorization,
and database interactions.

Functions:
    get_auth_service: Provides an instance of AuthService.
    get_user_service: Provides an instance of UserService.
    get_current_user: Retrieves the currently authenticated user.
    get_current_admin_user: Ensures the current user is an admin.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService
from src.entity.models import User, UserRole


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Provides an instance of AuthService.

    Args:
        db (AsyncSession): The database session.

    Returns:
        AuthService: An instance of the AuthService class.
    """
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Provides an instance of UserService.

    Args:
        db (AsyncSession): The database session.

    Returns:
        UserService: An instance of the UserService class.
    """
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Retrieves the currently authenticated user.

    Args:
        token (str): The JWT token provided by the user.
        auth_service (AuthService): The authentication service.

    Returns:
        User: The currently authenticated user.

    Raises:
        HTTPException: If the token is invalid or the user is not authenticated.
    """
    return await auth_service.get_current_user(token)


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the current user is an admin.

    Args:
        current_user (User): The currently authenticated user.

    Returns:
        User: The currently authenticated admin user.

    Raises:
        HTTPException: If the current user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission",
        )
    return current_user
