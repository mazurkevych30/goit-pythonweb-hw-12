"""Authentication and Authorization Routes.

This module provides routes for user authentication and authorization, including
registration, login, token refresh, and logout functionalities.
"""

import logging

from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.services.email import send_email
from src.schemas.token import TokenResponse, RefreshTokenRequest
from src.schemas.user import UserResponse, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("uvicorn.error")


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """Get an instance of the AuthService.

    Args:
        db (AsyncSession): The database session dependency.

    Returns:
        AuthService: An instance of the AuthService.
    """
    return AuthService(db)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user.

    Args:
        user_data (UserCreate): The user data for registration.
        background_tasks (BackgroundTasks): Background tasks for sending emails.
        request (Request): The HTTP request object.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        UserResponse: The registered user data.
    """
    user = await auth_service.register_user(user_data)
    background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    logger.info("User %s registered successfully", user.username)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate a user and generate access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): The login form data.
        request (Request, optional): The HTTP request object. Defaults to None.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        TokenResponse: The access and refresh tokens.
    """
    user = await auth_service.authenticate(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(user.username)
    refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: RefreshTokenRequest,
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access and refresh tokens.

    Args:
        refresh_token (RefreshTokenRequest): The refresh token request data.
        request (Request, optional): The HTTP request object. Defaults to None.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        TokenResponse: The new access and refresh tokens.
    """
    user = await auth_service.validate_refresh_token(refresh_token.refresh_token)

    new_access_token = auth_service.create_access_token(user.username)
    new_refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    await auth_service.revoke_refresh_token(refresh_token.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: RefreshTokenRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout a user by revoking access and refresh tokens.

    Args:
        refresh_token (RefreshTokenRequest): The refresh token to revoke.
        token (str): The access token to revoke.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        None
    """
    await auth_service.revoke_access_token(token)
    await auth_service.revoke_refresh_token(refresh_token.refresh_token)
    return None
