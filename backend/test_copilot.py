import pytest
from unittest.mock import patch, MagicMock
from backend.copilot.context_manager import assemble_tenant_copilot_context
from backend.copilot.copilot_engine import ask_copilot

# ---------------------------------------------------------
# Test Context Manager
# ---------------------------------------------------------
@patch("backend.copilot.context_manager.list_kpis")
@patch("backend.copilot.context_manager.list_integrations")
@patch("backend.copilot.context_manager.list_meetings")
def test_assemble_tenant_copilot_context_success(mock_meetings, mock_integrations, mock_kpis):
    mock_kpis.return_value = [{"id": "k-1", "name": "Active Users"}]
    mock_integrations.return_value = [
        {"id": "i-1", "name": "Notion", "status": "connected"},
        {"id": "i-2", "name": "Slack", "status": "disconnected"}
    ]
    mock_meetings.return_value = [{"id": "m-1", "title": "Weekly Planning"}]

    ctx = assemble_tenant_copilot_context("tenant-1")
    assert ctx["tenant_id"] == "tenant-1"
    assert ctx["kpi_count"] == 1
    assert ctx["kpis_list"] == ["Active Users"]
    assert ctx["active_integrations"] == ["Notion"]
    assert ctx["recent_meetings"] == ["Weekly Planning"]


@patch("backend.copilot.context_manager.list_kpis")
def test_assemble_tenant_copilot_context_exception(mock_kpis):
    mock_kpis.side_effect = Exception("DB error")
    ctx = assemble_tenant_copilot_context("tenant-1")
    assert ctx["tenant_id"] == "tenant-1"
    assert ctx["kpi_count"] == 0
    assert len(ctx["active_integrations"]) == 0


# ---------------------------------------------------------
# Test Copilot Engine
# ---------------------------------------------------------
@patch("backend.copilot.copilot_engine.SecretsManager.get_openai_api_key")
@patch("backend.copilot.copilot_engine.assemble_tenant_copilot_context")
@patch("backend.copilot.copilot_engine.search_memory")
def test_ask_copilot_no_api_key_fallbacks(mock_search, mock_ctx, mock_api_key):
    mock_api_key.return_value = None
    mock_search.return_value = [{"text": "memory snippet"}]
    mock_ctx.return_value = {
        "tenant_id": "tenant-1",
        "kpi_count": 2,
        "kpis_list": ["Users", "Sales"],
        "active_integrations": ["Slack"],
        "recent_meetings": []
    }

    # Test "sync" queries
    res_sync = ask_copilot("Trigger a sync job", "tenant-1", "admin")
    assert "active integrations" in res_sync["response"]

    # Test "kpi" queries
    res_kpi = ask_copilot("What are my kpis?", "tenant-1", "admin")
    assert "KPI metrics" in res_kpi["response"]

    # Test default query
    res_default = ask_copilot("Help me", "tenant-1", "admin")
    assert "How can I help you" in res_default["response"]


@patch("backend.copilot.copilot_engine.SecretsManager.get_openai_api_key")
@patch("backend.copilot.copilot_engine.assemble_tenant_copilot_context")
@patch("backend.copilot.copilot_engine.OpenAI")
def test_ask_copilot_with_api_key_json_response(mock_openai, mock_ctx, mock_api_key):
    mock_api_key.return_value = "fake-openai-key"
    mock_ctx.return_value = {"tenant_id": "t-1"}

    # Mock OpenAI completions client call returning valid JSON response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"response": "Sure, I triggered sync", "suggested_action": {"action": "sync"}}'
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    res = ask_copilot("sync notion", "tenant-1", "admin")
    assert res["response"] == "Sure, I triggered sync"
    assert res["suggested_action"] == {"action": "sync"}


@patch("backend.copilot.copilot_engine.SecretsManager.get_openai_api_key")
@patch("backend.copilot.copilot_engine.assemble_tenant_copilot_context")
@patch("backend.copilot.copilot_engine.OpenAI")
def test_ask_copilot_with_api_key_raw_text_response(mock_openai, mock_ctx, mock_api_key):
    mock_api_key.return_value = "fake-openai-key"
    mock_ctx.return_value = {"tenant_id": "t-1"}

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = 'Normal conversational response text from LLM'
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    res = ask_copilot("hello copilot", "tenant-1", "admin")
    assert res["response"] == "Normal conversational response text from LLM"
    assert res["suggested_action"] is None
