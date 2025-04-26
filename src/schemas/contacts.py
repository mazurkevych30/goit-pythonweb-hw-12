"""Schemas for contact-related operations.

This module defines Pydantic models for creating, updating, and responding with contact data.
It includes validation rules and optional fields for flexibility.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.conf import constants


class BaseContact(BaseModel):
    """Base schema for contact data.

    Defines common fields and validation rules for contact-related operations.
    """

    first_name: str = Field(
        max_length=constants.MAX_LENGTH_FIRST_NAME,
    )
    last_name: str = Field(
        max_length=constants.MAX_LENGTH_LAST_NAME,
    )
    email: str = Field(
        max_length=constants.MAX_LENGTH_EMAIL,
    )
    phone: str = Field(
        max_length=constants.MAX_LENGTH_PHONE,
        default=None,
    )
    birthday: date
    optional_data: Optional[str] = Field(
        max_length=constants.MAX_LENGTH_OPTIONAL_DATA,
        default=None,
    )


class CreateContact(BaseContact):
    """Schema for creating a new contact.

    Inherits from BaseContact and includes all required fields for contact creation.
    """

    pass


class UpdateContact(BaseContact):
    """Schema for updating an existing contact.

    Inherits from BaseContact but makes all fields optional to allow partial updates.
    """

    first_name: Optional[str] = Field(
        max_length=constants.MAX_LENGTH_FIRST_NAME,
        default=None,
    )
    last_name: Optional[str] = Field(
        max_length=constants.MAX_LENGTH_LAST_NAME,
        default=None,
    )
    email: Optional[str] = Field(
        max_length=constants.MAX_LENGTH_EMAIL,
        default=None,
    )
    phone: Optional[str] = Field(
        max_length=constants.MAX_LENGTH_PHONE,
        default=None,
    )
    birthday: Optional[date] = Field(default=None)
    optional_data: Optional[str] = Field(
        max_length=constants.MAX_LENGTH_OPTIONAL_DATA,
        default=None,
    )


class ContactResponse(BaseContact):
    """Schema for responding with contact data.

    Attributes:
        id (int): Unique identifier for the contact.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
