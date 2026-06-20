import uuid
import json
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection
from backend.integrations.connector_factory import ConnectorFactory
from backend.security.encryption import encrypt_value, decrypt_value, generate_encryption_key

# Global encryption key for storing credential settings securely.
# In production, this key would be fetched from SecretsManager vault.
_DB_SECRET_KEY = generate_encryption_key()

def create_integration(
    tenant_id: str,
    name: str,
    integration_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        integration_id = str(uuid.uuid4())
        
        # Encrypt the configuration payload before storing in database.
        config_str = json.dumps(config)
        encrypted_config = encrypt_value(_DB_SECRET_KEY, config_str)
        
        cur.execute(
            "INSERT INTO integrations (id, tenant_id, name, integration_type, config, status, created_at) "
            "VALUES (%s, %s, %s, %s, %s, 'disconnected', NOW())",
            (integration_id, tenant_id, name, integration_type, encrypted_config)
        )
        conn.commit()
        return {
            "id": integration_id,
            "tenant_id": tenant_id,
            "name": name,
            "integration_type": integration_type,
            "status": "disconnected"
        }

def list_integrations(tenant_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, integration_type, status, last_sync FROM integrations WHERE tenant_id = %s",
            (tenant_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "integration_type": row[2],
                "status": row[3],
                "last_sync": row[4].isoformat() if row[4] else None
            }
            for row in rows
        ]

def test_integration_connection(tenant_id: str, integration_id: str) -> bool:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT integration_type, config FROM integrations WHERE tenant_id = %s AND id = %s",
            (tenant_id, integration_id)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Integration not found")
            
        integration_type, encrypted_config = row
        config_str = decrypt_value(_DB_SECRET_KEY, encrypted_config)
        config = json.loads(config_str)
        
        connector = ConnectorFactory.get_connector(integration_type, config)
        is_ok = connector.test_connection()
        
        new_status = "connected" if is_ok else "error"
        cur.execute(
            "UPDATE integrations SET status = %s WHERE id = %s",
            (new_status, integration_id)
        )
        conn.commit()
        return is_ok

def trigger_sync(tenant_id: str, integration_id: str) -> Dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, integration_type, config FROM integrations WHERE tenant_id = %s AND id = %s",
            (tenant_id, integration_id)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Integration not found")
            
        name, integration_type, encrypted_config = row
        config_str = decrypt_value(_DB_SECRET_KEY, encrypted_config)
        config = json.loads(config_str)
        
        log_id = str(uuid.uuid4())
        try:
            connector = ConnectorFactory.get_connector(integration_type, config)
            records = connector.sync_data()
            records_count = len(records)
            
            cur.execute(
                "INSERT INTO sync_logs (id, tenant_id, integration_id, records_synced, status, timestamp) "
                "VALUES (%s, %s, %s, %s, 'success', NOW())",
                (log_id, tenant_id, integration_id, records_count)
            )
            cur.execute(
                "UPDATE integrations SET status = 'connected', last_sync = NOW() WHERE id = %s",
                (integration_id,)
            )
            conn.commit()
            return {"success": True, "records_synced": records_count, "log_id": log_id}
            
        except Exception as e:
            cur.execute(
                "INSERT INTO sync_logs (id, tenant_id, integration_id, records_synced, status, error_message, timestamp) "
                "VALUES (%s, %s, %s, 0, 'failed', %s, NOW())",
                (log_id, tenant_id, integration_id, str(e))
            )
            cur.execute(
                "UPDATE integrations SET status = 'error' WHERE id = %s",
                (integration_id,)
            )
            conn.commit()
            return {"success": False, "error": str(e), "log_id": log_id}

def get_sync_logs(tenant_id: str, integration_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, records_synced, status, error_message, timestamp FROM sync_logs "
            "WHERE tenant_id = %s AND integration_id = %s ORDER BY timestamp DESC LIMIT %s",
            (tenant_id, integration_id, limit)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "records_synced": row[1],
                "status": row[2],
                "error_message": row[3],
                "timestamp": row[4].isoformat() if row[4] else None
            }
            for row in rows
        ]
