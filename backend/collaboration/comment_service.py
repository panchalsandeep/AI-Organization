import uuid
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection

def create_comment(
    tenant_id: str,
    resource_type: str,
    resource_id: str,
    sender_id: str,
    sender_name: str,
    comment_text: str,
    parent_comment_id: Optional[str] = None
) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        comment_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO comments (id, tenant_id, resource_type, resource_id, parent_comment_id, sender_id, sender_name, comment_text, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())",
            (
                comment_id,
                tenant_id,
                resource_type,
                resource_id,
                parent_comment_id,
                sender_id,
                sender_name,
                comment_text
            )
        )
        conn.commit()
        return {
            "id": comment_id,
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "parent_comment_id": parent_comment_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "comment_text": comment_text
        }

def get_comments_for_resource(tenant_id: str, resource_type: str, resource_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, parent_comment_id, sender_id, sender_name, comment_text, created_at FROM comments "
            "WHERE tenant_id = %s AND resource_type = %s AND resource_id = %s ORDER BY created_at ASC",
            (tenant_id, resource_type, resource_id)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "parent_comment_id": row[1],
                "sender_id": row[2],
                "sender_name": row[3],
                "comment_text": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            }
            for row in rows
        ]
