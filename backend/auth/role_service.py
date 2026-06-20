import uuid
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection


def create_role(tenant_id: str, name: str, permissions: List[str]) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        role_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO roles (id, tenant_id, name, permissions, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (role_id, tenant_id, name, permissions)
        )
        conn.commit()
        return {
            "id": role_id,
            "tenant_id": tenant_id,
            "name": name,
            "permissions": permissions
        }


def assign_role_to_user(user_id: str, role_id: str, tenant_id: str) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        assignment_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO user_roles (id, user_id, role_id, tenant_id, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (assignment_id, user_id, role_id, tenant_id)
        )
        conn.commit()
        return {
            "id": assignment_id,
            "user_id": user_id,
            "role_id": role_id,
            "tenant_id": tenant_id
        }


def get_permissions_for_user(user_id: str, tenant_id: str) -> List[str]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT r.permissions FROM roles r JOIN user_roles ur ON ur.role_id = r.id WHERE ur.user_id = %s AND ur.tenant_id = %s",
            (user_id, tenant_id)
        )
        rows = cur.fetchall()
        permissions = []
        for row in rows:
            permissions.extend(row[0] or [])
    return list(set(permissions))


def list_roles(tenant_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, permissions, created_at FROM roles WHERE tenant_id = %s",
            (tenant_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "permissions": row[2] or [],
                "created_at": row[3].isoformat() if row[3] else None
            }
            for row in rows
        ]


def get_role(role_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, name, permissions, created_at FROM roles WHERE id = %s",
            (role_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "tenant_id": row[1],
            "name": row[2],
            "permissions": row[3] or [],
            "created_at": row[4].isoformat() if row[4] else None
        }
