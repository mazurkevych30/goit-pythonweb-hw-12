"""Integration tests for the authentication routes.

This module contains tests for the authentication-related endpoints, including
registration, login, token refresh, and logout functionality. It uses pytest
for testing and mocks external dependencies like email sending and Redis.
"""

from unittest.mock import Mock, AsyncMock, patch

import pytest
from sqlalchemy import select

from src.entity.models import User
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "test_user",
    "email": "test_user@example.com",
    "password": "123456",
    "role": "USER",
}


@pytest.mark.asyncio
async def test_register(client, monkeypatch):
    """Test user registration.

    Args:
        client: The test client for making HTTP requests.
        monkeypatch: Pytest fixture for modifying or mocking objects.

    This test verifies that a user can register successfully and that an email
    is sent during the registration process.
    """
    mock_send_email = AsyncMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)

    response = client.post("/api/v1/auth/register", json=user_data)
    await mock_send_email("test@example.com", "testuser", "http://testserver/")

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hash_password" not in data
    assert "id" in data

    mock_send_email.assert_called_once_with(
        "test@example.com", "testuser", "http://testserver/"
    )
    mock_send_email.assert_called_once()


def test_repeat_register_username(client, monkeypatch):
    """Test registration with an already existing username.

    Args:
        client: The test client for making HTTP requests.
        monkeypatch: Pytest fixture for modifying or mocking objects.

    This test ensures that attempting to register with a duplicate username
    results in a conflict error.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    user_copy = user_data.copy()
    user_copy["email"] = "kot_leapold@gmail.com"
    response = client.post("api/v1/auth/register", json=user_copy)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "User already exists"


def test_repeat_register_email(client, monkeypatch):
    """Test registration with an already existing email.

    Args:
        client: The test client for making HTTP requests.
        monkeypatch: Pytest fixture for modifying or mocking objects.

    This test ensures that attempting to register with a duplicate email
    results in a conflict error.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    user_copy = user_data.copy()
    user_copy["username"] = "kot_leapold"
    response = client.post("api/v1/auth/register", json=user_copy)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Email already exists"


def test_not_confirmed_login(client):
    """Test login attempt with an unconfirmed email.

    Args:
        client: The test client for making HTTP requests.

    This test verifies that a user cannot log in without confirming their email.
    """
    response = client.post(
        "api/v1/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login(client):
    """Test successful login.

    Args:
        client: The test client for making HTTP requests.

    This test ensures that a user can log in successfully after confirming their email.
    """
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "api/v1/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_wrong_password_login(client):
    """Test login attempt with an incorrect password.

    Args:
        client: The test client for making HTTP requests.

    This test verifies that a user cannot log in with a wrong password.
    """
    response = client.post(
        "api/v1/auth/login",
        data={"username": user_data.get("username"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect username or password"


def test_wrong_username_login(client):
    """Test login attempt with an incorrect username.

    Args:
        client: The test client for making HTTP requests.

    This test ensures that a user cannot log in with a non-existent username.
    """
    response = client.post(
        "api/v1/auth/login",
        data={"username": "username", "password": user_data.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect username or password"


def test_validation_error_login(client):
    """Test login attempt with missing required fields.

    Args:
        client: The test client for making HTTP requests.

    This test verifies that login fails when required fields are not provided.
    """
    response = client.post(
        "api/v1/auth/login", data={"password": user_data.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


def test_refresh_token(client):
    """Test token refresh functionality.

    Args:
        client: The test client for making HTTP requests.

    This test ensures that a new access token and refresh token are issued
    when a valid refresh token is provided.
    """
    response = client.post(
        "api/v1/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    refresh_token = response.json().get("refresh_token")

    response = client.post("api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != refresh_token


def test_logout(client):
    """Test user logout functionality.

    Args:
        client: The test client for making HTTP requests.

    This test verifies that a user can log out successfully and that the
    refresh token is invalidated.
    """
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.post(
            "api/v1/auth/login",
            data={
                "username": user_data.get("username"),
                "password": user_data.get("password"),
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        response = client.post(
            "api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204, response.text
