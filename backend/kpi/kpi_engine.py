import uuid
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection
from backend.multi_tenancy.tenant_context import get_tenant_id

def create_kpi(tenant_id: str, name: str, kpi_type: str, formula: Optional[str] = None, target_value: Optional[float] = None) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        kpi_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO kpis (id, tenant_id, name, kpi_type, formula, target_value, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (kpi_id, tenant_id, name, kpi_type, formula, target_value)
        )
        conn.commit()
        return {
            "id": kpi_id,
            "tenant_id": tenant_id,
            "name": name,
            "kpi_type": kpi_type,
            "formula": formula,
            "target_value": target_value
        }

def list_kpis(tenant_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, kpi_type, formula, target_value, created_at FROM kpis WHERE tenant_id = %s ORDER BY created_at DESC",
            (tenant_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "kpi_type": row[2],
                "formula": row[3],
                "target_value": float(row[4]) if row[4] is not None else None,
                "created_at": row[5].isoformat() if row[5] else None
            }
            for row in rows
        ]

def log_kpi_metric(tenant_id: str, kpi_id: str, value: float) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        metric_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO kpi_metrics (id, tenant_id, kpi_id, value, timestamp) VALUES (%s, %s, %s, %s, NOW())",
            (metric_id, tenant_id, kpi_id, value)
        )
        conn.commit()
        
        # Check target threshold alerts
        alert_triggered = False
        cur.execute("SELECT target_value, name FROM kpis WHERE id = %s", (kpi_id,))
        row = cur.fetchone()
        if row and row[0] is not None:
            target = float(row[0])
            name = row[1]
            if value < target:
                alert_triggered = True
                # In a real environment, we would also trigger a notification flow
                
        return {
            "id": metric_id,
            "tenant_id": tenant_id,
            "kpi_id": kpi_id,
            "value": value,
            "alert_triggered": alert_triggered
        }

def get_kpi_history(tenant_id: str, kpi_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, value, timestamp FROM kpi_metrics WHERE tenant_id = %s AND kpi_id = %s ORDER BY timestamp DESC LIMIT %s",
            (tenant_id, kpi_id, limit)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "value": float(row[1]),
                "timestamp": row[2].isoformat() if row[2] else None
            }
            for row in rows
        ]
