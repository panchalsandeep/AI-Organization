import pytest
from unittest.mock import patch, MagicMock
from backend.n8n_orchestrator.n8n_client import N8NClient
from backend.n8n_orchestrator.execution_monitor import get_execution_logs

def test_n8n_client_headers():
    client_no_key = N8NClient(api_key=None)
    headers = client_no_key.get_headers()
    assert "Content-Type" in headers
    assert "X-N8N-API-KEY" not in headers

    client_with_key = N8NClient(api_key="my-key")
    headers_with_key = client_with_key.get_headers()
    assert headers_with_key["X-N8N-API-KEY"] == "my-key"


@patch("requests.get")
def test_list_workflows_real_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "1", "name": "Sync", "active": True}]}
    mock_get.return_value = mock_response

    client = N8NClient()
    res = client.list_workflows()
    assert len(res) == 1
    assert res[0]["id"] == "1"


@patch("requests.get")
def test_list_workflows_fallback(mock_get):
    # Simulate timeout or error
    mock_get.side_effect = Exception("Connection timed out")

    client = N8NClient()
    res = client.list_workflows()
    assert len(res) == 3
    assert res[0]["id"] == "wf-sync-1"


@patch("requests.post")
def test_trigger_workflow_real_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_post.return_value = mock_response

    client = N8NClient()
    res = client.trigger_workflow("wf-1", {"test": "data"})
    assert res["status"] == "success"
    assert res["execution_id"] == "n8n-exec-real-123"
    assert res["data"] == {"status": "ok"}


@patch("requests.post")
def test_trigger_workflow_fallback(mock_post):
    mock_post.side_effect = Exception("Connection failure")

    client = N8NClient()
    res = client.trigger_workflow("wf-1", {"test": "data"})
    assert res["status"] == "success"
    assert "mocked" in res
    assert res["execution_id"] == "n8n-mock-exec-wf-1"


def test_get_execution_logs():
    logs = get_execution_logs("wf-1")
    assert len(logs) == 2
    assert logs[0]["workflow_id"] == "wf-1"
    assert logs[0]["status"] == "success"
    assert logs[1]["status"] == "failed"
    assert "error" in logs[1]
