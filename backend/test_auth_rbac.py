import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from datetime import timedelta
from jose import jwt
from backend.auth.authentication import (
    create_access_token,
    get_current_user,
    require_permission,
    authenticate_credentials,
    SECRET_KEY,
    ALGORITHM,
)
from backend.auth.user_service import authenticate_user, User
from backend.auth.role_service import (
    create_role,
    assign_role_to_user,
    get_permissions_for_user,
    list_roles,
    get_role,
)

# ---------------------------------------------------------
# Test Token Utilities
# ---------------------------------------------------------
def test_create_and_decode_access_token():
    payload = {"sub": "user-123", "permissions": ["tenant:read"]}
    token = create_access_token(payload, expires_delta=timedelta(minutes=10))

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user-123"
    assert decoded["permissions"] == ["tenant:read"]
    assert "exp" in decoded


def test_get_current_user_valid_token():
    payload = {"sub": "user-123", "permissions": ["tenant:read"]}
    token = create_access_token(payload)

    user = get_current_user(token)
    assert user["user_id"] == "user-123"
    assert user["permissions"] == ["tenant:read"]


def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        get_current_user("invalid-token-string")
    assert exc.value.status_code == 401


# ---------------------------------------------------------
# Test User Auth Logic
# ---------------------------------------------------------
def test_authenticate_user_success():
    user = authenticate_user("admin", "admin123")
    assert user is not None
    assert user.username == "admin"
    assert "tenant:read" in user.permissions


def test_authenticate_user_failure():
    user = authenticate_user("admin", "wrong-password")
    assert user is None


def test_authenticate_credentials_success():
    creds = authenticate_credentials("admin", "admin123")
    assert creds["sub"] == "e10b5e63-1a96-4c2e-b72a-a182a0cc9c8f"
    assert creds["username"] == "admin"


def test_authenticate_credentials_failure():
    with pytest.raises(HTTPException) as exc:
        authenticate_credentials("admin", "wrong")
    assert exc.value.status_code == 401


# ---------------------------------------------------------
# Test Permission Guard Decorator
# ---------------------------------------------------------
def test_require_permission_success():
    checker = require_permission("tenant:read")
    user = {"user_id": "u-1", "permissions": ["tenant:read", "tenant:write"]}
    result = checker(current_user=user)
    assert result == user


def test_require_permission_failure():
    checker = require_permission("tenant:write")
    user = {"user_id": "u-1", "permissions": ["tenant:read"]}
    with pytest.raises(HTTPException) as exc:
        checker(current_user=user)
    assert exc.value.status_code == 403


# ---------------------------------------------------------
# Test RBAC Database Service
# ---------------------------------------------------------
@patch("backend.auth.role_service.get_connection")
def test_create_role(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    role = create_role("tenant-1", "Analyst", ["kpi:read", "audit:read"])
    assert role["name"] == "Analyst"
    assert role["permissions"] == ["kpi:read", "audit:read"]
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("backend.auth.role_service.get_connection")
def test_assign_role_to_user(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    assignment = assign_role_to_user("user-a", "role-b", "tenant-c")
    assert assignment["user_id"] == "user-a"
    assert assignment["role_id"] == "role-b"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("backend.auth.role_service.get_connection")
def test_get_permissions_for_user(mock_get_conn):
    mock_cursor = MagicMock()
    # Mock user having multiple roles with permissions
    mock_cursor.fetchall.return_value = [
        (["kpi:read", "kpi:write"],),
        (["audit:read"],)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    permissions = get_permissions_for_user("user-x", "tenant-y")
    assert set(permissions) == {"kpi:read", "kpi:write", "audit:read"}
    mock_cursor.execute.assert_called_once()


@patch("backend.auth.role_service.get_connection")
def test_list_roles(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("r-1", "Admin", ["tenant:write"], None),
        ("r-2", "Viewer", ["tenant:read"], None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    roles = list_roles("tenant-1")
    assert len(roles) == 2
    assert roles[0]["name"] == "Admin"
    assert roles[1]["permissions"] == ["tenant:read"]


@patch("backend.auth.role_service.get_connection")
def test_get_role(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("r-1", "tenant-1", "Admin", ["tenant:write"], None)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    role = get_role("r-1")
    assert role is not None
    assert role["name"] == "Admin"
    assert role["permissions"] == ["tenant:write"]
