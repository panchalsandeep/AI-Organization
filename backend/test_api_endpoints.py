import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.auth.authentication import create_access_token

client = TestClient(app)

# Helper to create a test token with specific permissions
def get_auth_headers(permissions):
    token = create_access_token({"sub": "test-user-id", "permissions": permissions})
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "test-tenant-id",
        "X-Tenant-Name": "Test Tenant"
    }

# ---------------------------------------------------------
# Test Health Endpoints
# ---------------------------------------------------------
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Operations API Running" in response.json()["status"]

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ---------------------------------------------------------
# Test Auth Token Endpoint
# ---------------------------------------------------------
@patch("backend.api.main.authenticate_credentials")
def test_get_token(mock_auth):
    mock_auth.return_value = {
        "sub": "user-123",
        "username": "admin",
        "permissions": ["tenant:read", "tenant:write"]
    }
    response = client.post("/auth/token", data={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# ---------------------------------------------------------
# Test Tenant Endpoints
# ---------------------------------------------------------
@patch("backend.api.main.create_tenant")
@patch("backend.api.main.log_audit_event")
def test_create_tenant_endpoint(mock_log, mock_create):
    mock_create.return_value = {"id": "t-1", "name": "A", "organization_id": "o-1", "status": "active"}
    headers = get_auth_headers(["tenant:write"])
    response = client.post("/admin/tenant", json={"tenant_name": "A", "organization_id": "o-1"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["tenant"]["id"] == "t-1"
    mock_create.assert_called_once_with(name="A", organization_id="o-1")
    mock_log.assert_called_once()

@patch("backend.api.main.get_tenant")
def test_get_tenant_endpoint(mock_get):
    mock_get.return_value = {"id": "t-1", "name": "A", "organization_id": "o-1", "status": "active"}
    headers = get_auth_headers(["tenant:read"])
    response = client.get("/admin/tenant/t-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["tenant"]["name"] == "A"

@patch("backend.api.main.get_tenant")
def test_get_tenant_not_found(mock_get):
    mock_get.return_value = None
    headers = get_auth_headers(["tenant:read"])
    response = client.get("/admin/tenant/missing", headers=headers)
    assert response.status_code == 404

@patch("backend.api.main.list_tenants")
def test_list_tenants_endpoint(mock_list):
    mock_list.return_value = [{"id": "t-1", "name": "A"}]
    headers = get_auth_headers(["tenant:read"])
    response = client.get("/admin/tenants", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1


# ---------------------------------------------------------
# Test RBAC Endpoints
# ---------------------------------------------------------
@patch("backend.api.main.create_role")
@patch("backend.api.main.log_audit_event")
def test_create_role_endpoint(mock_log, mock_create):
    mock_create.return_value = {"id": "r-1", "tenant_id": "t-1", "name": "Analyst", "permissions": ["kpi:read"]}
    headers = get_auth_headers(["role:write"])
    response = client.post("/admin/role", json={"role_name": "Analyst", "permissions": ["kpi:read"]}, headers=headers)
    assert response.status_code == 200
    assert response.json()["role"]["id"] == "r-1"

@patch("backend.api.main.list_roles")
def test_list_roles_endpoint(mock_list):
    mock_list.return_value = [{"id": "r-1", "name": "Analyst"}]
    headers = get_auth_headers(["role:read"])
    response = client.get("/admin/roles", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1

@patch("backend.api.main.assign_role_to_user")
@patch("backend.api.main.log_audit_event")
def test_assign_role_endpoint(mock_log, mock_assign):
    mock_assign.return_value = {"id": "a-1", "user_id": "u-1", "role_id": "r-1", "tenant_id": "t-1"}
    headers = get_auth_headers(["role:write"])
    response = client.post("/admin/assign-role", json={"user_id": "u-1", "role_id": "r-1"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

@patch("backend.api.main.get_permissions_for_user")
def test_get_user_permissions_endpoint(mock_get_perms):
    mock_get_perms.return_value = ["kpi:read"]
    headers = get_auth_headers(["role:read"])
    response = client.get("/admin/user/u-1/permissions", headers=headers)
    assert response.status_code == 200
    assert response.json()["permissions"] == ["kpi:read"]


# ---------------------------------------------------------
# Test Audit & Compliance Endpoints
# ---------------------------------------------------------
@patch("backend.api.main.get_audit_events")
def test_list_audit_events(mock_get_events):
    # Mock row fields returned from get_audit_events
    mock_get_events.return_value = [
        ("log-1", "user-1", "action-1", "res-type", "res-id", {}, "127.0.0.1", {}, "2026-06-20T12:00:00")
    ]
    headers = get_auth_headers(["audit:read"])
    response = client.get("/admin/audit/events", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["events"][0]["id"] == "log-1"

@patch("backend.api.main.get_compliance_events")
def test_list_compliance_events(mock_get_events):
    mock_get_events.return_value = [
        ("comp-1", "SOC2_CHECK", "compliant", {}, "2026-06-20T12:00:00")
    ]
    headers = get_auth_headers(["compliance:read"])
    response = client.get("/admin/compliance/events", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["events"][0]["id"] == "comp-1"

@patch("backend.api.main.record_compliance_event")
@patch("backend.api.main.log_audit_event")
def test_create_compliance_event(mock_log, mock_record):
    headers = get_auth_headers(["compliance:write"])
    response = client.post(
        "/admin/compliance/event",
        json={"event_type": "SOC2_CHECK", "status": "compliant", "details": {"scope": "access"}},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_record.assert_called_once_with(event_type="SOC2_CHECK", status="compliant", details={"scope": "access"})


# ---------------------------------------------------------
# Test KPI Endpoints (Sprint 2)
# ---------------------------------------------------------
@patch("backend.api.main.create_kpi")
@patch("backend.api.main.log_audit_event")
def test_create_kpi_route(mock_log, mock_create):
    mock_create.return_value = {"id": "k-1", "name": "Users", "kpi_type": "number"}
    headers = get_auth_headers(["kpi:write"])
    response = client.post("/kpi", json={"name": "Users", "kpi_type": "number"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["kpi"]["id"] == "k-1"

@patch("backend.api.main.list_kpis")
def test_list_kpis_route(mock_list):
    mock_list.return_value = [{"id": "k-1", "name": "Users"}]
    headers = get_auth_headers(["kpi:read"])
    response = client.get("/kpis", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1

@patch("backend.api.main.get_kpi_history")
@patch("backend.api.main.log_kpi_metric")
@patch("backend.api.main.kpi_manager.broadcast_to_tenant")
def test_log_kpi_metric_route(mock_broadcast, mock_log, mock_history):
    mock_log.return_value = {"id": "m-1", "alert_triggered": True}
    mock_history.return_value = []
    headers = get_auth_headers(["kpi:write"])
    response = client.post("/kpi/metric", json={"kpi_id": "k-1", "value": 45.5}, headers=headers)
    assert response.status_code == 200
    assert response.json()["metric"]["id"] == "m-1"
    mock_broadcast.assert_called_once()

@patch("backend.api.main.get_kpi_history")
def test_get_kpi_history_route(mock_hist):
    mock_hist.return_value = [{"id": "m-1", "value": 12.0}]
    headers = get_auth_headers(["kpi:read"])
    response = client.get("/kpi/k-1/history?limit=10", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["history"]) == 1

@patch("backend.api.main.aggregate_kpi_metrics")
def test_get_kpi_aggregation_route(mock_agg):
    mock_agg.return_value = [{"time_bucket": "2026-06-20", "avg_value": 3.0}]
    headers = get_auth_headers(["kpi:read"])
    response = client.get("/kpi/k-1/aggregation?interval=day", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["aggregations"]) == 1


# ---------------------------------------------------------
# Test Meeting Intelligence Endpoints (Sprint 2)
# ---------------------------------------------------------
@patch("backend.api.main.transcribe_audio")
@patch("backend.api.main.generate_meeting_summary")
@patch("backend.api.main.extract_action_items")
@patch("backend.api.main.create_meeting")
@patch("backend.api.main.log_audit_event")
def test_process_meeting_route(mock_log, mock_create, mock_extract, mock_summary, mock_transcribe):
    mock_transcribe.return_value = "Audio text"
    mock_summary.return_value = "Summary text"
    mock_extract.return_value = []
    mock_create.return_value = {"id": "m-1", "title": "Review"}
    
    headers = get_auth_headers(["meeting:write"])
    response = client.post("/meeting", json={"title": "Review", "duration_seconds": 60}, headers=headers)
    assert response.status_code == 200
    assert response.json()["meeting"]["id"] == "m-1"

@patch("backend.api.main.get_meeting")
def test_get_meeting_route(mock_get):
    mock_get.return_value = {"id": "m-1", "title": "Review"}
    headers = get_auth_headers(["meeting:read"])
    response = client.get("/meeting/m-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["meeting"]["title"] == "Review"

@patch("backend.api.main.list_meetings")
def test_list_meetings_route(mock_list):
    mock_list.return_value = [{"id": "m-1", "title": "Review"}]
    headers = get_auth_headers(["meeting:read"])
    response = client.get("/meetings", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1


# ---------------------------------------------------------
# Test Collaboration Endpoints (Sprint 2)
# ---------------------------------------------------------
@patch("backend.api.main.create_comment")
def test_create_comment_route(mock_create):
    mock_create.return_value = {"id": "c-1", "comment_text": "Nice"}
    headers = get_auth_headers(["user:write"])
    response = client.post("/comment", json={"resource_type": "kpi", "resource_id": "k-1", "comment_text": "Nice"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["comment"]["id"] == "c-1"

@patch("backend.api.main.get_comments_for_resource")
def test_list_comments_route(mock_list):
    mock_list.return_value = [{"id": "c-1", "comment_text": "Nice"}]
    headers = get_auth_headers(["user:read"])
    response = client.get("/comments/kpi/k-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1

@patch("backend.api.main.get_chat_history")
def test_get_chat_history_route(mock_history):
    mock_history.return_value = [{"id": "msg-1", "message_text": "Hello"}]
    headers = get_auth_headers(["user:read"])
    response = client.get("/chat/room-1/history?limit=10", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["history"]) == 1


# ---------------------------------------------------------
# Test Integrations Endpoints (Sprint 3)
# ---------------------------------------------------------
@patch("backend.api.main.create_integration")
@patch("backend.api.main.log_audit_event")
def test_create_integration_route(mock_log, mock_create):
    mock_create.return_value = {"id": "int-1", "name": "Slack App", "integration_type": "slack", "status": "disconnected"}
    headers = get_auth_headers(["integration:write"])
    response = client.post("/integration", json={"name": "Slack App", "integration_type": "slack", "config": {"bot_token": "xoxb-1"}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["integration"]["id"] == "int-1"
    mock_create.assert_called_once_with(tenant_id="test-tenant-id", name="Slack App", integration_type="slack", config={"bot_token": "xoxb-1"})
    mock_log.assert_called_once()


@patch("backend.api.main.list_integrations")
def test_list_integrations_route(mock_list):
    mock_list.return_value = [{"id": "int-1", "name": "Slack App", "integration_type": "slack", "status": "connected", "last_sync": None}]
    headers = get_auth_headers(["integration:read"])
    response = client.get("/integrations", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["count"] == 1


@patch("backend.api.main.test_integration_connection")
def test_test_integration_connection_route(mock_test):
    mock_test.return_value = True
    headers = get_auth_headers(["integration:write"])
    response = client.post("/integration/int-1/test", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["connected"] is True


@patch("backend.api.main.trigger_sync")
@patch("backend.api.main.log_audit_event")
def test_trigger_integration_sync_route(mock_log, mock_sync):
    mock_sync.return_value = {"success": True, "records_synced": 4}
    headers = get_auth_headers(["integration:write"])
    response = client.post("/integration/int-1/sync", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["sync"]["records_synced"] == 4
    mock_log.assert_called_once()


@patch("backend.api.main.get_sync_logs")
def test_get_integration_sync_logs_route(mock_logs):
    mock_logs.return_value = [{"id": "log-1", "records_synced": 4, "status": "success", "error_message": None, "timestamp": None}]
    headers = get_auth_headers(["integration:read"])
    response = client.get("/integration/int-1/sync-logs", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["logs"]) == 1


# ---------------------------------------------------------
# Test n8n Automation Endpoints (Sprint 3)
# ---------------------------------------------------------
@patch("backend.n8n_orchestrator.n8n_client.N8NClient.list_workflows")
def test_list_n8n_workflows_route(mock_list):
    mock_list.return_value = [{"id": "wf-1", "name": "Sync", "active": True}]
    headers = get_auth_headers(["workflow:manage"])
    response = client.get("/automation/n8n/workflows", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["count"] == 1


@patch("backend.n8n_orchestrator.n8n_client.N8NClient.trigger_workflow")
def test_trigger_n8n_workflow_route(mock_trigger):
    mock_trigger.return_value = {"status": "success", "execution_id": "exec-1"}
    headers = get_auth_headers(["workflow:execute"])
    response = client.post("/automation/n8n/trigger", json={"workflow_id": "wf-1", "payload": {"foo": "bar"}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["result"]["execution_id"] == "exec-1"


@patch("backend.api.main.get_execution_logs")
def test_get_n8n_execution_logs_route(mock_logs):
    mock_logs.return_value = [{"execution_id": "exec-1", "status": "success", "started_at": "", "finished_at": "", "duration_seconds": 1}]
    headers = get_auth_headers(["workflow:manage"])
    response = client.get("/automation/n8n/wf-1/logs", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["logs"]) == 1


# ---------------------------------------------------------
# Test AI Copilot Endpoints (Sprint 3)
# ---------------------------------------------------------
@patch("backend.api.main.ask_copilot")
def test_ask_copilot_route(mock_ask):
    mock_ask.return_value = {"response": "Answer", "suggested_action": None, "context": {}}
    headers = get_auth_headers(["user:read"])
    response = client.post("/copilot/ask", json={"query": "Hello"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["result"]["response"] == "Answer"


# ---------------------------------------------------------
# Test Decision Intelligence Endpoints (Sprint 3 Extension)
# ---------------------------------------------------------
@patch("backend.api.main.create_decision")
@patch("backend.api.main.log_audit_event")
def test_create_decision_route(mock_log, mock_create):
    mock_create.return_value = {"id": "d-1", "title": "Migrate Database"}
    headers = get_auth_headers(["decision:write"])
    response = client.post(
        "/decision",
        json={"title": "Migrate Database", "description": "Migrating", "estimated_impact": 4},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["decision"]["id"] == "d-1"
    mock_log.assert_called_once()

@patch("backend.api.main.list_decisions")
def test_list_decisions_route(mock_list):
    mock_list.return_value = [{"id": "d-1", "title": "Migrate Database"}]
    headers = get_auth_headers(["decision:read"])
    response = client.get("/decisions", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["decisions"][0]["id"] == "d-1"

@patch("backend.api.main.get_decision")
def test_get_decision_route_success(mock_get):
    mock_get.return_value = {"id": "d-1", "title": "Migrate"}
    headers = get_auth_headers(["decision:read"])
    response = client.get("/decision/d-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["decision"]["title"] == "Migrate"

@patch("backend.api.main.get_decision")
def test_get_decision_route_not_found(mock_get):
    mock_get.return_value = None
    headers = get_auth_headers(["decision:read"])
    response = client.get("/decision/missing", headers=headers)
    assert response.status_code == 404

@patch("backend.api.main.update_decision")
@patch("backend.api.main.log_audit_event")
def test_update_decision_route(mock_log, mock_update):
    mock_update.return_value = {"id": "d-1", "title": "Migrate", "status": "evaluated"}
    headers = get_auth_headers(["decision:write"])
    response = client.put(
        "/decision/d-1",
        json={"title": "Migrate", "description": "Migrating", "status": "evaluated", "estimated_impact": 4, "actual_impact": 4, "outcome": "Success"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["decision"]["status"] == "evaluated"
    mock_log.assert_called_once()

@patch("backend.api.main.delete_decision")
@patch("backend.api.main.log_audit_event")
def test_delete_decision_route(mock_log, mock_delete):
    mock_delete.return_value = True
    headers = get_auth_headers(["decision:write"])
    response = client.delete("/decision/d-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_log.assert_called_once()

# ---------------------------------------------------------
# Test Wiki Endpoints (Sprint 3 Extension)
# ---------------------------------------------------------

@patch("backend.api.main.create_wiki_page")
@patch("backend.api.main.log_audit_event")
def test_create_wiki_route(mock_log, mock_create):
    mock_create.return_value = {"id": "w-1", "title": "SOC2 Guidelines", "slug": "soc2-guidelines", "version": 1}
    headers = get_auth_headers(["wiki:write"])
    response = client.post("/wiki", json={"title": "SOC2 Guidelines", "slug": "soc2-guidelines", "content": "Guides", "tags": ["sec"]}, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["page"]["id"] == "w-1"
    mock_log.assert_called_once()

@patch("backend.api.main.list_wiki_pages")
def test_list_wiki_route(mock_list):
    mock_list.return_value = [{"id": "w-1", "title": "SOC2 Guidelines"}]
    headers = get_auth_headers(["wiki:read"])
    response = client.get("/wiki/pages", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["count"] == 1

@patch("backend.api.main.get_wiki_page")
def test_get_wiki_route(mock_get):
    mock_get.return_value = {"id": "w-1", "title": "SOC2 Guidelines"}
    headers = get_auth_headers(["wiki:read"])
    response = client.get("/wiki/page/w-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["page"]["title"] == "SOC2 Guidelines"

@patch("backend.api.main.get_wiki_page")
def test_get_wiki_route_not_found(mock_get):
    mock_get.return_value = None
    headers = get_auth_headers(["wiki:read"])
    response = client.get("/wiki/page/missing", headers=headers)
    assert response.status_code == 404

@patch("backend.api.main.update_wiki_page")
@patch("backend.api.main.log_audit_event")
def test_update_wiki_route(mock_log, mock_update):
    mock_update.return_value = {"id": "w-1", "title": "SOC2 Updated", "slug": "soc2-updated", "version": 2}
    headers = get_auth_headers(["wiki:write"])
    response = client.put(
        "/wiki/page/w-1",
        json={"title": "SOC2 Updated", "slug": "soc2-updated", "content": "Updated content", "tags": ["sec"]},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["page"]["version"] == 2
    mock_log.assert_called_once()

@patch("backend.api.main.delete_wiki_page")
@patch("backend.api.main.log_audit_event")
def test_delete_wiki_route(mock_log, mock_delete):
    mock_delete.return_value = True
    headers = get_auth_headers(["wiki:write"])
    response = client.delete("/wiki/page/w-1", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_log.assert_called_once()

@patch("backend.api.main.get_wiki_page_history")
def test_get_wiki_history_route(mock_hist):
    mock_hist.return_value = [{"id": "h-1", "version": 1}]
    headers = get_auth_headers(["wiki:read"])
    response = client.get("/wiki/page/w-1/history", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["history"]) == 1

@patch("backend.api.main.search_memory")
@patch("backend.api.main.search_wiki_text")
def test_search_wiki_route(mock_search_text, mock_search_memory):
    mock_search_text.return_value = [{"id": "w-1", "title": "SOC2"}]
    mock_search_memory.return_value = [
        {
            "title": "SOC2 Guidelines Document",
            "content_type": "wiki",
            "similarity": 0.88,
            "metadata": {
                "tenant_id": "test-tenant-id",
                "wiki_page_id": "w-1"
            }
        }
    ]
    headers = get_auth_headers(["wiki:read"])
    response = client.get("/wiki/search?q=SOC2", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["results"]) == 1
    assert len(response.json()["recommendations"]) == 1
    assert response.json()["recommendations"][0]["title"] == "SOC2 Guidelines Document"



