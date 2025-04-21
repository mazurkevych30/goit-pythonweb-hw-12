from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService


def get_auth_service(db: AsyncSession = Depends(get_db)):
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)):
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(token)
