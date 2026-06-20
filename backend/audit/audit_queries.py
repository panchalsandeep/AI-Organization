from typing import List, Optional
from backend.database.postgres_client import get_connection


def get_audit_events(tenant_id: str, limit: int = 100, offset: int = 0):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, user_id, action, resource_type, resource_id, changes, ip_address, metadata, created_at FROM audit_logs WHERE tenant_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (tenant_id, limit, offset)
        )
        return cur.fetchall()


def get_compliance_events(tenant_id: str, limit: int = 100, offset: int = 0):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, event_type, status, details, created_at FROM compliance_events WHERE tenant_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (tenant_id, limit, offset)
        )
        return cur.fetchall()
