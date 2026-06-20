import json
from datetime import datetime
from typing import Dict, Any, Optional
from backend.database.postgres_client import get_connection
from backend.multi_tenancy.tenant_context import get_tenant_id


def log_audit_event(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    tenant_id = get_tenant_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO audit_logs (id, tenant_id, user_id, action, resource_type, resource_id, changes, ip_address, metadata, created_at) VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
            (
                tenant_id,
                user_id,
                action,
                resource_type,
                resource_id,
                json.dumps(changes or {}),
                ip_address,
                json.dumps(metadata or {}),
            )
        )
        conn.commit()
