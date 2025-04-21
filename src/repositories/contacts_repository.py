import logging

from datetime import date, timedelta

from typing import Sequence

from sqlalchemy import select, or_, extract, and_

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contacts import BaseContact, UpdateContact

logger = logging.getLogger("uvicorn.error")


class ContactsRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(
        self, user: User, limit: int, offset: int
    ) -> Sequence[Contact]:

        query = select(Contact).filter_by(user_id=user.id).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_contact_by_id(self, user: User, contact_id: int) -> Contact | None:

        query = select(Contact).filter_by(id=contact_id, user_id=user.id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_contact(self, user: User, body: BaseContact) -> Contact:

        new_contact = Contact(**body.model_dump(), user=user)
        self.db.add(new_contact)
        await self.db.commit()
        await self.db.refresh(new_contact)
        return new_contact

    async def update_contact(
        self, user: User, contact_id: int, body: UpdateContact
    ) -> Contact | None:
        contact = await self.get_contact_by_id(user, contact_id)
        if contact:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def remove_contact(self, user: User, contact_id: int) -> Contact | None:

        contact = await self.get_contact_by_id(user, contact_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(
        self, user: User, query: str, limit: int = 10, offset: int = 0
    ) -> Sequence[Contact]:
        query = (
            select(Contact)
            .where(
                and_(
                    Contact.user_id == user.id,
                    or_(
                        Contact.first_name.ilike(f"%{query}%"),
                        Contact.last_name.ilike(f"%{query}%"),
                        Contact.email.ilike(f"%{query}%"),
                        Contact.phone.ilike(f"%{query}%"),
                    ),
                )
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_birthdays(
        self, user: User, days_ahead: int = 7
    ) -> Sequence[Contact]:
        today = date.today()
        upcoming_birthday = today + timedelta(days=days_ahead)

        query = select(Contact).where(
            and_(
                Contact.user_id == user.id,
                or_(
                    and_(
                        extract("month", Contact.birthday) == today.month,
                        extract("day", Contact.birthday) >= today.day,
                    ),
                    and_(
                        extract("month", Contact.birthday) == upcoming_birthday.month,
                        extract("day", Contact.birthday) <= upcoming_birthday.day,
                    ),
                    and_(
                        extract("month", Contact.birthday) > today.month,
                        extract("month", Contact.birthday) < upcoming_birthday.month,
                    ),
                ),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
