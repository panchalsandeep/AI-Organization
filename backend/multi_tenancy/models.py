from pydantic import BaseModel
from typing import Optional, Dict, Any


class Tenant(BaseModel):
    id: str
    name: str
    organization_id: str
    status: str
    created_at: Optional[str]
    metadata: Optional[Dict[str, Any]] = {}
