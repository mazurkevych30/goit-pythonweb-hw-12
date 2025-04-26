"""Contacts Service Module

This module provides the ContactsService class, which acts as a service layer for managing contacts.
It interacts with the ContactsRepository to perform CRUD operations and other contact-related functionalities.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.contacts_repository import ContactsRepository

from src.entity.models import User
from src.schemas.contacts import BaseContact, UpdateContact


class ContactsService:
    """Service class for managing contacts.

    This class provides methods to create, retrieve, update, delete, and search contacts, as well as retrieve upcoming birthdays.
    It interacts with the ContactsRepository to perform database operations.

    Attributes:
        contacts_repository (ContactsRepository): The repository instance for managing contact data.
    """

    def __init__(self, db: AsyncSession):
        """Initialize ContactsService with a database session.

        Args:
            db (AsyncSession): The asynchronous database session.
        """
        self.contacts_repository = ContactsRepository(db)

    async def create_contact(self, body: BaseContact, user: User):
        """Create a new contact for a user.

        Args:
            body (BaseContact): The contact data to create.
            user (User): The user creating the contact.

        Returns:
            The created contact instance.
        """
        return await self.contacts_repository.create_contact(user, body)

    async def get_contacts(self, limit: int, offset: int, user: User):
        """Retrieve a list of contacts for a user with pagination.

        Args:
            limit (int): The maximum number of contacts to retrieve.
            offset (int): The number of contacts to skip.
            user (User): The user whose contacts are being retrieved.

        Returns:
            A list of contact instances.
        """
        return await self.contacts_repository.get_contacts(user, limit, offset)

    async def ge_contact_by_id(self, contact_id: int, user: User):
        """Retrieve a contact by its ID for a user.

        Args:
            contact_id (int): The ID of the contact to retrieve.
            user (User): The user whose contact is being retrieved.

        Returns:
            The contact instance if found, otherwise None.
        """
        return await self.contacts_repository.get_contact_by_id(user, contact_id)

    async def update_contact(self, contact_id: int, body: UpdateContact, user: User):
        """Update an existing contact for a user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (UpdateContact): The updated contact data.
            user (User): The user updating the contact.

        Returns:
            The updated contact instance.
        """
        return await self.contacts_repository.update_contact(user, contact_id, body)

    async def remove_contact(self, contact_id: int, user: User):
        """Remove a contact by its ID for a user.

        Args:
            contact_id (int): The ID of the contact to remove.
            user (User): The user removing the contact.

        Returns:
            The removed contact instance if successful, otherwise None.
        """
        return await self.contacts_repository.remove_contact(user, contact_id)

    async def search_contacts(self, query: str, limit: int, offset: int, user: User):
        """Search for contacts matching a query for a user.

        Args:
            query (str): The search query string.
            limit (int): The maximum number of contacts to retrieve.
            offset (int): The number of contacts to skip.
            user (User): The user whose contacts are being searched.

        Returns:
            A list of contact instances matching the query.
        """
        return await self.contacts_repository.search_contacts(
            query=query, limit=limit, offset=offset, user=user
        )

    async def get_upcoming_birthdays(self, user: User, days_ahead: int):
        """Retrieve contacts with upcoming birthdays within a specified number of days.

        Args:
            user (User): The user whose contacts are being checked.
            days_ahead (int): The number of days ahead to check for birthdays.

        Returns:
            A list of contact instances with upcoming birthdays.
        """
        return await self.contacts_repository.get_upcoming_birthdays(user, days_ahead)
