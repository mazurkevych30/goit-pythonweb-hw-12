"""Utility module for password hashing.

This module provides functionality to securely hash passwords using the bcrypt library.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password as a string.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()
