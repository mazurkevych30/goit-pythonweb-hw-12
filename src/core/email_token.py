"""
Utility functions for creating and decoding email verification tokens.

This module provides helper functions for generating JWT tokens for
email verification and extracting email addresses from these tokens.

Functions:
    create_email_token: Generates a JWT token for email verification.
    get_email_from_token: Decodes a JWT token to extract the email address.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf.config import settings


def create_email_token(data: dict) -> str:
    """Generates a JWT token for email verification.

    Args:
        data (dict): A dictionary containing the payload data for the token.
                     Typically includes the email address as "sub".

    Returns:
        str: A JWT token encoded with the provided data and expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """Decodes a JWT token to extract the email address.

    Args:
        token (str): The JWT token to decode.

    Returns:
        str: The email address extracted from the token.

    Raises:
        HTTPException: If the token is invalid or cannot be decoded.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload["sub"]
        return email
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email verification token",
        ) from e
