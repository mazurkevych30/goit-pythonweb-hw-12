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
    return await auth_service.get_current_user(token)


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, user_service: UserService = Depends(get_user_service)
):
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
    # current_user: User = Depends(get_current_user),
):
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
    await user_service.change_password(token, body.new_password)
    return {"message": "Password changed successfully"}
