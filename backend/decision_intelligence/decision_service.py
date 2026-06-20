import uuid
import json
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection

def create_decision(
    tenant_id: str,
    title: str,
    description: str,
    context: Optional[str],
    alternatives: List[str],
    status: str,
    estimated_impact: int,
    created_by: str
) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        decision_id = str(uuid.uuid4())
        alternatives_json = json.dumps(alternatives)
        
        cur.execute(
            "INSERT INTO decisions (id, tenant_id, title, description, context, alternatives, status, estimated_impact, created_by, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
            (decision_id, tenant_id, title, description, context, alternatives_json, status, estimated_impact, created_by)
        )
        conn.commit()
        
        return {
            "id": decision_id,
            "tenant_id": tenant_id,
            "title": title,
            "description": description,
            "context": context,
            "alternatives": alternatives,
            "status": status,
            "estimated_impact": estimated_impact,
            "created_by": created_by
        }

def list_decisions(tenant_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, description, context, alternatives, status, estimated_impact, actual_impact, outcome, created_by, created_at, updated_at, decided_at "
            "FROM decisions WHERE tenant_id = %s ORDER BY created_at DESC",
            (tenant_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "context": row[3],
                "alternatives": json.loads(row[4]) if isinstance(row[4], str) else (row[4] if row[4] else []),
                "status": row[5],
                "estimated_impact": row[6],
                "actual_impact": row[7],
                "outcome": row[8],
                "created_by": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None,
                "decided_at": row[12].isoformat() if row[12] else None
            }
            for row in rows
        ]

def get_decision(tenant_id: str, decision_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, description, context, alternatives, status, estimated_impact, actual_impact, outcome, created_by, created_at, updated_at, decided_at "
            "FROM decisions WHERE tenant_id = %s AND id = %s",
            (tenant_id, decision_id)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "context": row[3],
            "alternatives": json.loads(row[4]) if isinstance(row[4], str) else (row[4] if row[4] else []),
            "status": row[5],
            "estimated_impact": row[6],
            "actual_impact": row[7],
            "outcome": row[8],
            "created_by": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None,
            "decided_at": row[12].isoformat() if row[12] else None
        }

def update_decision(
    tenant_id: str,
    decision_id: str,
    title: str,
    description: str,
    context: Optional[str],
    alternatives: List[str],
    status: str,
    estimated_impact: int,
    actual_impact: Optional[int],
    outcome: Optional[str]
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM decisions WHERE tenant_id = %s AND id = %s", (tenant_id, decision_id))
        if not cur.fetchone():
            return None
            
        alternatives_json = json.dumps(alternatives)
        decided_at_clause = ""
        if status in ("decided", "implemented", "evaluated"):
            decided_at_clause = ", decided_at = COALESCE(decided_at, NOW())"
            
        cur.execute(
            f"UPDATE decisions "
            f"SET title = %s, description = %s, context = %s, alternatives = %s, status = %s, "
            f"    estimated_impact = %s, actual_impact = %s, outcome = %s, updated_at = NOW() {decided_at_clause} "
            f"WHERE tenant_id = %s AND id = %s",
            (title, description, context, alternatives_json, status, estimated_impact, actual_impact, outcome, tenant_id, decision_id)
        )
        conn.commit()
        return get_decision(tenant_id, decision_id)

def delete_decision(tenant_id: str, decision_id: str) -> bool:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM decisions WHERE tenant_id = %s AND id = %s", (tenant_id, decision_id))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
