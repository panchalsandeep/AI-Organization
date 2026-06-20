from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class KPIDefinition(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    name: str
    kpi_type: str # 'number', 'percentage', 'currency'
    formula: Optional[str] = None
    target_value: Optional[float] = None
    created_at: Optional[str] = None

class KPIMetricLog(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    kpi_id: str
    value: float
    timestamp: Optional[str] = None
