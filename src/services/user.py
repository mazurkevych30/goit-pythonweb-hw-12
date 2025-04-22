from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from fastapi import HTTPException, status

from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService
from src.conf.config import settings
from src.util.hash_password import hash_password

redis_client = redis.from_url(settings.REDIS_URL)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        user = await self.user_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        return await self.user_repository.update_avatar_url(email, url)

    async def change_password(self, token: str, new_password: str) -> None:
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
        await redis_client.setex(f"reset_token:{token}", 900, email)

    async def get_email_from_redis(self, token: str) -> str | None:
        email = await redis_client.get(f"reset_token:{token}")
        return email.decode() if email else None

    async def delete_token_from_redis(self, token: str) -> None:
        await redis_client.delete(f"reset_token:{token}")
