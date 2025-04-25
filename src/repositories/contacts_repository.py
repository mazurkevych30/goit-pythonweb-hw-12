"""
Repository for contact-related database operations.

This module defines the `ContactsRepository` class, which provides methods
for performing CRUD operations and other contact-specific database interactions.

Classes:
    ContactsRepository: A repository for managing contact-related database operations.
"""

import logging
from datetime import date, timedelta
from typing import Sequence

from sqlalchemy import select, or_, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contacts import BaseContact, UpdateContact

logger = logging.getLogger("uvicorn.error")


class ContactsRepository:
    """A repository for managing contact-related database operations.

    This class provides methods for retrieving, creating, updating, deleting,
    and searching contacts, as well as retrieving upcoming birthdays.
    """

    def __init__(self, session: AsyncSession):
        """Initializes the ContactsRepository with a database session.

        Args:
            session (AsyncSession): The database session.
        """
        self.db = session

    async def get_contacts(
        self, user: User, limit: int, offset: int
    ) -> Sequence[Contact]:
        """Retrieves a paginated list of contacts for a specific user.

        Args:
            user (User): The user whose contacts are being retrieved.
            limit (int): The maximum number of contacts to retrieve.
            offset (int): The number of contacts to skip.

        Returns:
            Sequence[Contact]: A list of contacts belonging to the user.
        """
        query = select(Contact).filter_by(user_id=user.id).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_contact_by_id(self, user: User, contact_id: int) -> Contact | None:
        """Retrieves a specific contact by its ID for a given user.

        Args:
            user (User): The user who owns the contact.
            contact_id (int): The ID of the contact to retrieve.

        Returns:
            Contact | None: The contact if found, or None if not found.
        """
        query = select(Contact).filter_by(id=contact_id, user_id=user.id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_contact(self, user: User, body: BaseContact) -> Contact:
        """Creates a new contact for a specific user.

        Args:
            user (User): The user who owns the contact.
            body (BaseContact): The data for the new contact.

        Returns:
            Contact: The created contact instance.
        """
        new_contact = Contact(**body.model_dump(), user=user)
        self.db.add(new_contact)
        await self.db.commit()
        await self.db.refresh(new_contact)
        return new_contact

    async def update_contact(
        self, user: User, contact_id: int, body: UpdateContact
    ) -> Contact | None:
        """Updates an existing contact for a specific user.

        Args:
            user (User): The user who owns the contact.
            contact_id (int): The ID of the contact to update.
            body (UpdateContact): The updated data for the contact.

        Returns:
            Contact | None: The updated contact if found, or None if not found.
        """
        contact = await self.get_contact_by_id(user, contact_id)
        if contact:
            update_data = body.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, user: User, contact_id: int) -> Contact | None:
        """Deletes a contact for a specific user.

        Args:
            user (User): The user who owns the contact.
            contact_id (int): The ID of the contact to delete.

        Returns:
            Contact | None: The deleted contact if found, or None if not found.
        """
        contact = await self.get_contact_by_id(user, contact_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(
        self, user: User, query: str, limit: int = 10, offset: int = 0
    ) -> Sequence[Contact]:
        """Searches for contacts by name, email, or phone for a specific user.

        Args:
            user (User): The user who owns the contacts.
            query (str): The search query string.
            limit (int, optional): The maximum number of contacts to retrieve. Defaults to 10.
            offset (int, optional): The number of contacts to skip. Defaults to 0.

        Returns:
            Sequence[Contact]: A list of contacts matching the search query.
        """
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
        """Retrieves contacts with upcoming birthdays within a specified number of days.

        Args:
            user (User): The user who owns the contacts.
            days_ahead (int, optional): The number of days ahead to check for birthdays. Defaults to 7.

        Returns:
            Sequence[Contact]: A list of contacts with upcoming birthdays.
        """
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
