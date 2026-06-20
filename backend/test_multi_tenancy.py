import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from backend.multi_tenancy.tenant_context import (
    set_tenant_context,
    get_tenant_id,
    get_tenant_name,
    clear_tenant_context,
)
from backend.multi_tenancy.tenant_router import TenantRouterMiddleware
from backend.multi_tenancy.tenant_service import (
    create_tenant,
    get_tenant,
    list_tenants,
)

# ---------------------------------------------------------
# Test Context Variables
# ---------------------------------------------------------
def test_tenant_context_management():
    clear_tenant_context()
    assert get_tenant_id() is None
    assert get_tenant_name() is None

    set_tenant_context("tenant-123", "Acme Corp")
    assert get_tenant_id() == "tenant-123"
    assert get_tenant_name() == "Acme Corp"

    clear_tenant_context()
    assert get_tenant_id() is None
    assert get_tenant_name() is None


# ---------------------------------------------------------
# Test Router Middleware
# ---------------------------------------------------------
app = FastAPI()
app.add_middleware(TenantRouterMiddleware)

@app.get("/")
def home():
    return {"message": "hello"}

@app.get("/guarded")
def guarded_endpoint():
    return {"tenant_id": get_tenant_id(), "tenant_name": get_tenant_name()}

client = TestClient(app)

def test_middleware_exempt_path():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}

def test_middleware_missing_tenant_header():
    # If exempt path is not used and header is missing, it should fail
    response = client.get("/guarded")
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing X-Tenant-ID header"

def test_middleware_with_tenant_header():
    response = client.get("/guarded", headers={"X-Tenant-ID": "t-1", "X-Tenant-Name": "Tenant One"})
    assert response.status_code == 200
    assert response.json() == {"tenant_id": "t-1", "tenant_name": "Tenant One"}


# ---------------------------------------------------------
# Test Tenant Database Service
# ---------------------------------------------------------
@patch("backend.multi_tenancy.tenant_service.get_connection")
def test_create_tenant(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    tenant = create_tenant(name="New Tenant", organization_id="org-123", metadata={"tier": "enterprise"})

    assert tenant["name"] == "New Tenant"
    assert tenant["organization_id"] == "org-123"
    assert "id" in tenant
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("backend.multi_tenancy.tenant_service.get_connection")
def test_get_tenant(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("tenant-id-abc", "Acme", "org-555", "active", None, {"x": 1})
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    tenant = get_tenant("tenant-id-abc")

    assert tenant is not None
    assert tenant["id"] == "tenant-id-abc"
    assert tenant["name"] == "Acme"
    assert tenant["status"] == "active"
    assert tenant["metadata"] == {"x": 1}
    mock_cursor.execute.assert_called_once_with(
        "SELECT id, name, organization_id, status, created_at, metadata FROM tenants WHERE id = %s",
        ("tenant-id-abc",)
    )


@patch("backend.multi_tenancy.tenant_service.get_connection")
def test_get_tenant_not_found(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    tenant = get_tenant("non-existent")
    assert tenant is None


@patch("backend.multi_tenancy.tenant_service.get_connection")
def test_list_tenants(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("t-1", "Tenant A", "org-a", "active", None, {}),
        ("t-2", "Tenant B", "org-b", "suspended", None, {})
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    tenants = list_tenants()
    assert len(tenants) == 2
    assert tenants[0]["id"] == "t-1"
    assert tenants[1]["status"] == "suspended"
