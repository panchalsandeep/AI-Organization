import uuid
from typing import Dict, Any, Optional
from backend.database.postgres_client import get_connection


def create_tenant(name: str, organization_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        tenant_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO tenants (id, name, organization_id, status, created_at, metadata) VALUES (%s, %s, %s, %s, NOW(), %s)",
            (tenant_id, name, organization_id, "active", metadata)
        )
        conn.commit()
        return {
            "id": tenant_id,
            "name": name,
            "organization_id": organization_id,
            "status": "active",
            "metadata": metadata or {}
        }


def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, organization_id, status, created_at, metadata FROM tenants WHERE id = %s",
            (tenant_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "organization_id": row[2],
            "status": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "metadata": row[5] or {}
        }


def list_tenants() -> list[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, organization_id, status, created_at, metadata FROM tenants ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "organization_id": row[2],
                "status": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "metadata": row[5] or {}
            }
            for row in rows
        ]
