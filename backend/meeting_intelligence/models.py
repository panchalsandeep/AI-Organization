import uuid
import json
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection

def create_meeting(
    tenant_id: str,
    title: str,
    duration_seconds: int = 0,
    transcript_text: Optional[str] = None,
    summary: Optional[str] = None,
    action_items: Optional[List[Dict[str, Any]]] = None,
    audio_url: Optional[str] = None
) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        meeting_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO meetings (id, tenant_id, title, date, duration_seconds, transcript_text, summary, action_items, audio_url, created_at) "
            "VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, NOW())",
            (
                meeting_id,
                tenant_id,
                title,
                duration_seconds,
                transcript_text,
                summary,
                json.dumps(action_items or []),
                audio_url
            )
        )
        conn.commit()
        return {
            "id": meeting_id,
            "tenant_id": tenant_id,
            "title": title,
            "duration_seconds": duration_seconds,
            "transcript_text": transcript_text,
            "summary": summary,
            "action_items": action_items or [],
            "audio_url": audio_url
        }

def get_meeting(meeting_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, tenant_id, title, date, duration_seconds, transcript_text, summary, action_items, audio_url FROM meetings WHERE id = %s",
            (meeting_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "tenant_id": row[1],
            "title": row[2],
            "date": row[3].isoformat() if row[3] else None,
            "duration_seconds": row[4],
            "transcript_text": row[5],
            "summary": row[6],
            "action_items": row[7] if isinstance(row[7], list) else json.loads(row[7] or "[]"),
            "audio_url": row[8]
        }

def list_meetings(tenant_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, date, duration_seconds, summary, audio_url FROM meetings WHERE tenant_id = %s ORDER BY date DESC",
            (tenant_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "date": row[2].isoformat() if row[2] else None,
                "duration_seconds": row[3],
                "summary": row[4],
                "audio_url": row[5]
            }
            for row in rows
        ]
