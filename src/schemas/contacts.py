from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.conf import constants


class BaseContact(BaseModel):
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
    pass


class UpdateContact(BaseContact):
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
    id: int

    model_config = ConfigDict(from_attributes=True)
