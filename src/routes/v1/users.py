"""User Management Routes.

This module provides routes for managing user-related operations, including
retrieving user details, confirming email, updating avatars, and handling
password reset requests.
"""

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    status,
    BackgroundTasks,
    File,
    UploadFile,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.conf.config import settings
from src.core.email_token import get_email_from_token
from src.core.reset_token import create_reset_token
from src.core.depend_service import (
    get_auth_service,
    get_user_service,
    get_current_user,
    get_current_admin_user,
)
from src.entity.models import User
from src.schemas.user import UserResponse
from src.schemas.email import RequestEmail
from src.schemas.password import ResetPasswordRequest
from src.services.auth import AuthService, oauth2_scheme
from src.services.upload_file import UploadFileService
from src.services.user import UserService
from src.services.email import send_email, send_reset_password_email


router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
async def me(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Retrieve the current authenticated user's details.

    Args:
        request (Request): The HTTP request object.
        token (str): The access token for authentication.
        auth_service (AuthService): The authentication service dependency.

    Returns:
        UserResponse: The details of the current user.
    """
    return await auth_service.get_current_user(token)


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, user_service: UserService = Depends(get_user_service)
):
    """Confirm a user's email using a token.

    Args:
        token (str): The email confirmation token.
        user_service (UserService): The user service dependency.

    Returns:
        dict: A message indicating the confirmation status.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    email = get_email_from_token(token)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed"
        )
    if user.confirmed:
        return {"message": "Email already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed successfully"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """Request an email confirmation for a user.

    Args:
        body (RequestEmail): The email request payload.
        background_tasks (BackgroundTasks): Background tasks for sending emails.
        request (Request): The HTTP request object.
        user_service (UserService): The user service dependency.

    Returns:
        dict: A message indicating the email request status.
    """
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Email already confirmed"}
    if user:
        background_tasks.add_task(
            send_email, body.email, user.username, request.base_url
        )
        return {"message": "Confirmation email sent"}


@router.patch("/avatar", response_model=UserResponse)
async def update_user_avatar(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update the avatar of the current user.

    Args:
        file (UploadFile): The uploaded avatar file.
        user (User): The current authenticated admin user.
        user_service (UserService): The user service dependency.

    Returns:
        UserResponse: The updated user details with the new avatar URL.
    """
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user = await user_service.update_avatar_url(user.email, avatar_url)
    return user


@router.post("/request_reset_password")
async def request_reset_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """Request a password reset for a user.

    Args:
        body (RequestEmail): The email request payload.
        background_tasks (BackgroundTasks): Background tasks for sending emails.
        request (Request): The HTTP request object.
        user_service (UserService): The user service dependency.

    Returns:
        dict: A message indicating the password reset email status.
    """
    user = await user_service.get_user_by_email(body.email)

    if user is None:
        return {"message": "Wrong email, please check your email"}

    if user:
        token = create_reset_token({"sub": user.email})
        await user_service.save_token_to_redis(user.email, token)
        background_tasks.add_task(
            send_reset_password_email,
            body.email,
            user.username,
            request.base_url,
            token,
        )
        return {"message": "Reset password email sent"}


@router.patch("/reset_password/{token}")
async def reset_password(
    token: str,
    body: ResetPasswordRequest,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """Reset a user's password using a token.

    Args:
        token (str): The password reset token.
        body (ResetPasswordRequest): The new password payload.
        user_service (UserService): The user service dependency.
        current_user (User): The current authenticated user.

    Returns:
        dict: A message indicating the password reset status.
    """
    await user_service.change_password(token, body.new_password)
    return {"message": "Password changed successfully"}
