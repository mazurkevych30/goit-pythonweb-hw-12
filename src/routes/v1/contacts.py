"""Contacts Management Routes.

This module provides routes for managing user contacts, including creating,
retrieving, updating, deleting, and searching contacts, as well as retrieving
upcoming birthdays.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.depend_service import get_current_user
from src.database.db import get_db
from src.entity.models import User
from src.services.contacts import ContactsService
from src.schemas.contacts import BaseContact, UpdateContact, ContactResponse


router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger("uvicorn.error")


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieve a list of contacts for the current user.

    Args:
        limit (int): The maximum number of contacts to retrieve.
        offset (int): The number of contacts to skip.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        list[ContactResponse]: A list of contacts.
    """
    contacts_service = ContactsService(db)
    return await contacts_service.get_contacts(limit, offset, user)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieve a specific contact by ID.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        ContactResponse: The contact details.

    Raises:
        HTTPException: If the contact is not found.
    """
    contacts_service = ContactsService(db)
    contact = await contacts_service.ge_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: BaseContact,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new contact for the current user.

    Args:
        body (BaseContact): The contact data to create.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        ContactResponse: The created contact details.
    """
    contact_service = ContactsService(db)
    return await contact_service.create_contact(body, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: UpdateContact,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an existing contact for the current user.

    Args:
        contact_id (int): The ID of the contact to update.
        body (UpdateContact): The updated contact data.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        ContactResponse: The updated contact details.

    Raises:
        HTTPException: If the contact is not found.
    """
    contact_secvice = ContactsService(db)
    contact = await contact_secvice.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a contact for the current user.

    Args:
        contact_id (int): The ID of the contact to delete.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        None
    """
    contact_secvice = ContactsService(db)
    await contact_secvice.remove_contact(contact_id, user)
    return None


@router.get("/search/", response_model=list[ContactResponse])
async def search_contacts(
    query: str,
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Search for contacts by a query string.

    Args:
        query (str): The search query string.
        limit (int): The maximum number of contacts to retrieve.
        offset (int): The number of contacts to skip.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        list[ContactResponse]: A list of matching contacts.
    """
    contact_secvice = ContactsService(db)
    return await contact_secvice.search_contacts(query, limit, offset, user)


@router.get("/upcoming_birthdays/", response_model=list[ContactResponse])
async def get_upcoming_birthdays(
    days_ahead: int = Query(7, ge=1, le=31),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieve contacts with upcoming birthdays within a specified number of days.

    Args:
        days_ahead (int): The number of days ahead to check for birthdays.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user.

    Returns:
        list[ContactResponse]: A list of contacts with upcoming birthdays.
    """
    contact_secvice = ContactsService(db)
    return await contact_secvice.get_upcoming_birthdays(user, days_ahead)
