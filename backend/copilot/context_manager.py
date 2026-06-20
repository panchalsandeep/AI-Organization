from typing import Dict, Any
from backend.multi_tenancy.tenant_context import get_tenant_id
from backend.kpi.kpi_engine import list_kpis
from backend.integrations.sync_manager import list_integrations
from backend.meeting_intelligence.models import list_meetings

def assemble_tenant_copilot_context(tenant_id: str) -> Dict[str, Any]:
    """
    Assemble the complete status context for a tenant.
    Includes active KPIs list, integrations setup, and processed meetings.
    """
    try:
        kpis = list_kpis(tenant_id)
        integrations = list_integrations(tenant_id)
        meetings = list_meetings(tenant_id)
    except Exception:
        kpis, integrations, meetings = [], [], []

    return {
        "tenant_id": tenant_id,
        "kpi_count": len(kpis),
        "kpis_list": [k["name"] for k in kpis],
        "active_integrations": [i["name"] for i in integrations if i["status"] == "connected"],
        "recent_meetings": [m["title"] for m in meetings[:3]]
    }
