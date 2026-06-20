import uuid
from fastapi import WebSocket
from typing import List, Dict, Any
from backend.database.postgres_client import get_connection

class ChatRoomManager:
    def __init__(self):
        # (tenant_id, room_id) -> list of WebSockets
        self.active_rooms: Dict[tuple, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str, room_id: str):
        await websocket.accept()
        key = (tenant_id, room_id)
        if key not in self.active_rooms:
            self.active_rooms[key] = []
        self.active_rooms[key].append(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str, room_id: str):
        key = (tenant_id, room_id)
        if key in self.active_rooms:
            if websocket in self.active_rooms[key]:
                self.active_rooms[key].remove(websocket)

    async def broadcast_to_room(self, tenant_id: str, room_id: str, message: Any):
        key = (tenant_id, room_id)
        if key in self.active_rooms:
            for connection in self.active_rooms[key]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

chat_manager = ChatRoomManager()

def save_chat_message(
    tenant_id: str,
    room_id: str,
    sender_id: str,
    sender_name: str,
    message_text: str
) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        message_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO chat_messages (id, tenant_id, room_id, sender_id, sender_name, message_text, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (message_id, tenant_id, room_id, sender_id, sender_name, message_text)
        )
        conn.commit()
        return {
            "id": message_id,
            "tenant_id": tenant_id,
            "room_id": room_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "message_text": message_text
        }

def get_chat_history(tenant_id: str, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, sender_id, sender_name, message_text, created_at FROM chat_messages "
            "WHERE tenant_id = %s AND room_id = %s ORDER BY created_at ASC LIMIT %s",
            (tenant_id, room_id, limit)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "sender_id": row[1],
                "sender_name": row[2],
                "message_text": row[3],
                "created_at": row[4].isoformat() if row[4] else None
            }
            for row in rows
        ]
