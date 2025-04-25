"""
Configuration settings for the application.

This module defines the `Settings` class, which manages application
configuration using environment variables. It includes settings for:
- Database connection.
- JWT authentication.
- Redis configuration.
- Email service.
- Cloudinary integration.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict, EmailStr


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        DB_URL (str): The database connection URL.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Expiration time for access tokens in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS (int): Expiration time for refresh tokens in days.
        ALGORITHM (str): The algorithm used for JWT encoding/decoding.
        SECRET_KEY (str): The secret key for JWT.
        REDIS_URL (str): The Redis connection URL.
        MAIL_USERNAME (EmailStr): The email address used for sending emails.
        MAIL_PASSWORD (str): The password for the email account.
        MAIL_FROM (EmailStr): The sender's email address.
        MAIL_PORT (int): The port for the email server.
        MAIL_SERVER (str): The email server address.
        MAIL_FROM_NAME (str): The name displayed as the sender.
        MAIL_STARTTLS (bool): Whether to use STARTTLS for email.
        MAIL_SSL_TLS (bool): Whether to use SSL/TLS for email.
        USE_CREDENTIALS (bool): Whether to use credentials for email authentication.
        VALIDATE_CERTS (bool): Whether to validate SSL certificates for email.
        CLD_NAME (str): The Cloudinary account name.
        CLD_API_KEY (str): The Cloudinary API key.
        CLD_API_SECRET (str): The Cloudinary API secret.
        model_config (ConfigDict): Pydantic configuration for environment variables.
    """

    DB_URL: str
    # jwt
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str
    SECRET_KEY: str
    # redis
    REDIS_URL: str = "redis://localhost"
    # email
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    # cloudinary
    CLD_NAME: str
    CLD_API_KEY: str
    CLD_API_SECRET: str

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
"""
Instance of the Settings class.

This object is used throughout the application to access configuration
settings loaded from environment variables.
"""
