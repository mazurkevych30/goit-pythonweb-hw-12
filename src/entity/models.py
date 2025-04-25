"""
Database models for the application.

This module defines the SQLAlchemy ORM models used in the application.
These models represent the database schema and include relationships
between entities such as users, contacts, and refresh tokens.

Classes:
    UserRole: Enum representing user roles (USER, ADMIN).
    Base: Base class for all SQLAlchemy models.
    Contact: Represents a contact entity in the database.
    User: Represents a user entity in the database.
    RefreshToken: Represents a refresh token entity in the database.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    String,
    DateTime,
    Date,
    func,
    ForeignKey,
    Text,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.conf import constants


class UserRole(str, Enum):
    """Enum representing user roles.

    Attributes:
        USER (str): Regular user role.
        ADMIN (str): Admin user role.
    """

    USER = "USER"
    ADMIN = "ADMIN"


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class Contact(Base):
    """Represents a contact entity in the database.

    Attributes:
        id (int): Primary key of the contact.
        first_name (str): First name of the contact.
        last_name (str): Last name of the contact.
        email (str): Email address of the contact.
        phone (str): Phone number of the contact (optional).
        birthday (datetime): Birthday of the contact.
        optional_data (str): Additional optional data about the contact.
        created_at (datetime): Timestamp when the contact was created.
        updated_at (datetime): Timestamp when the contact was last updated.
        user_id (int): Foreign key referencing the associated user.
        user (User): Relationship to the associated user.
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(
        String(constants.MAX_LENGTH_FIRST_NAME), nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(constants.MAX_LENGTH_LAST_NAME), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(constants.MAX_LENGTH_EMAIL), nullable=False, unique=True
    )
    phone: Mapped[str] = mapped_column(
        String(constants.MAX_LENGTH_PHONE), nullable=True
    )
    birthday: Mapped[datetime] = mapped_column(Date, nullable=False)
    optional_data: Mapped[str] = mapped_column(
        String(constants.MAX_LENGTH_OPTIONAL_DATA), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")


class User(Base):
    """Represents a user entity in the database.

    Attributes:
        id (int): Primary key of the user.
        username (str): Username of the user.
        email (str): Email address of the user.
        hash_password (str): Hashed password of the user.
        role (UserRole): Role of the user (USER or ADMIN).
        avatar (str): URL of the user's avatar (optional).
        confirmed (bool): Whether the user's email is confirmed.
        refresh_tokens (list[RefreshToken]): List of associated refresh tokens.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    hash_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.USER, nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )


class RefreshToken(Base):
    """Represents a refresh token entity in the database.

    Attributes:
        id (int): Primary key of the refresh token.
        user_id (int): Foreign key referencing the associated user.
        token_hash (str): Hashed value of the refresh token.
        created_at (datetime): Timestamp when the token was created.
        expires_at (datetime): Timestamp when the token will expire.
        revoked_at (datetime): Timestamp when the token was revoked (optional).
        ip_address (str): IP address from which the token was issued (optional).
        user_agent (str): User agent string of the client (optional).
        user (User): Relationship to the associated user.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
