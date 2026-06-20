from pydantic import BaseModel
from typing import Optional, Dict, Any


class AuditLog(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    changes: Optional[Dict[str, Any]] = {}
    ip_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[str] = None


class ComplianceEvent(BaseModel):
    id: str
    tenant_id: str
    event_type: str
    status: str
    details: Optional[Dict[str, Any]] = {}
    created_at: Optional[str] = None
