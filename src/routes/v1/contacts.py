import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.depend_service import get_current_user
from src.database.db import get_db
from src.entity.models import User
from src.services.contacts import ContactsService
from src.schemas.contacts import BaseContact, UpdateContact


router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger("uvicorn.error")


@router.get("/", response_model=list[BaseContact])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contacts_service = ContactsService(db)
    return await contacts_service.get_contacts(limit, offset, user)


@router.get("/{contact_id}", response_model=BaseContact)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contacts_service = ContactsService(db)
    contact = await contacts_service.ge_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with id {contact_id} not found",
        )
    return contact


@router.post("/", response_model=BaseContact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: BaseContact,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_service = ContactsService(db)
    return await contact_service.create_contact(body, user)


@router.put("/{contact_id}", response_model=BaseContact)
async def update_contact(
    contact_id: int,
    body: UpdateContact,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_secvice = ContactsService(db)
    contact = await contact_secvice.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with id {contact_id} not found",
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_secvice = ContactsService(db)
    await contact_secvice.remove_contact(contact_id, user)
    return None


@router.get("/search/", response_model=list[BaseContact])
async def search_contacts(
    query: str,
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_secvice = ContactsService(db)
    return await contact_secvice.search_contacts(query, limit, offset, user)


@router.get("/upcoming_birthdays/", response_model=list[BaseContact])
async def get_upcoming_birthdays(
    days_ahead: int = Query(7, ge=1, le=31),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contact_secvice = ContactsService(db)
    return await contact_secvice.get_upcoming_birthdays(days_ahead, user)
