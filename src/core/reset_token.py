"""
Utility functions for creating password reset tokens.

This module provides a helper function for generating JWT tokens
used in password reset functionality.

Functions:
    create_reset_token: Generates a JWT token for password reset.
"""

from datetime import datetime, timedelta, timezone
import jwt

from src.conf.config import settings


def create_reset_token(data: dict) -> str:
    """Generates a JWT token for password reset.

    Args:
        data (dict): A dictionary containing the payload data for the token.
                     Typically includes the user's email as "sub".

    Returns:
        str: A JWT token encoded with the provided data and expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token
