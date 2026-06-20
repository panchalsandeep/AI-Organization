from typing import Dict, Any
from backend.database.postgres_client import get_connection
from backend.multi_tenancy.tenant_context import get_tenant_id


def record_compliance_event(
    event_type: str,
    status: str,
    details: Dict[str, Any]
) -> None:
    tenant_id = get_tenant_id()
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO compliance_events (id, tenant_id, event_type, status, details, created_at) VALUES (gen_random_uuid(), %s, %s, %s, %s, NOW())",
            (tenant_id, event_type, status, details)
        )
        conn.commit()
