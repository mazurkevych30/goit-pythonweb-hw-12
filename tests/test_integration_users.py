from unittest.mock import patch, Mock, AsyncMock

import pytest

from conftest import test_user


def test_me(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data
        assert "id" in data
        assert data["username"] == test_user["username"]


@patch("src.services.upload_file.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.get.return_value = None
        fake_url = "http://example.com/avatar.jpg"
        mock_upload_file.return_value = fake_url

        headers = {"Authorization": f"Bearer {get_token}"}

        file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

        response = client.patch(
            "/api/v1/users/avatar", headers=headers, files=file_data
        )

        assert response.status_code == 200, response.text

        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert data["avatar"] == fake_url

        mock_upload_file.assert_called_once()


@patch("src.services.user.redis_client")
@pytest.mark.asyncio
async def test_request_reset_password(
    mock_redis_client, client, monkeypatch, get_token
):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_reset_password_email", mock_send_email)
    mock_redis_client.setex.return_value = None

    email = test_user["email"]
    response = client.post(
        "/api/v1/users/request_reset_password",
        json={"email": email},
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Reset password email sent"


@patch("src.services.user.redis_client")
@pytest.mark.asyncio
async def test_request_reset_password_invalid_email(
    mock_redis_client, client, monkeypatch, get_token
):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_reset_password_email", mock_send_email)
    mock_redis_client.setex.return_value = None

    invalid_email = "nonexistent@example.com"
    response = client.post(
        "/api/v1/users/request_reset_password",
        json={"email": invalid_email},
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Wrong email, please check your email"


@patch("src.services.user.redis_client")
@patch("src.services.auth.redis_client")
@pytest.mark.asyncio
async def test_reset_password(
    mock_auth_redis, mock_redis_client, client, monkeypatch, get_token
):
    mock_change_password = AsyncMock()
    monkeypatch.setattr(
        "src.services.user.UserService.change_password", mock_change_password
    )
    mock_auth_redis.exists.return_value = False
    mock_auth_redis.get.return_value = None
    mock_redis_client.get.return_value = test_user["email"].encode()
    mock_redis_client.delete.return_value = True

    token = "valid_reset_token"
    new_password = "new_secure_password"

    response = client.patch(
        f"/api/v1/users/reset_password/{token}",
        json={"new_password": new_password},
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Password changed successfully"

    mock_change_password.assert_awaited_once_with(token, new_password)
