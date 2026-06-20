import pytest
import json
from unittest.mock import patch, MagicMock
from backend.audit.audit_logger import log_audit_event
from backend.audit.compliance_engine import record_compliance_event
from backend.audit.audit_queries import get_audit_events, get_compliance_events

# ---------------------------------------------------------
# Test Audit Logging
# ---------------------------------------------------------
@patch("backend.audit.audit_logger.get_tenant_id")
@patch("backend.audit.audit_logger.get_connection")
def test_log_audit_event(mock_get_conn, mock_get_tenant_id):
    mock_get_tenant_id.return_value = "tenant-xyz"
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    log_audit_event(
        user_id="user-111",
        action="kpi:create",
        resource_type="kpi",
        resource_id="kpi-999",
        changes={"value": 10},
        ip_address="127.0.0.1",
        metadata={"source": "api"}
    )

    mock_cursor.execute.assert_called_once()
    args, kwargs = mock_cursor.execute.call_args
    query_str = args[0]
    query_params = args[1]

    # Verify query params match expected values
    assert "INSERT INTO audit_logs" in query_str
    assert query_params[0] == "tenant-xyz"
    assert query_params[1] == "user-111"
    assert query_params[2] == "kpi:create"
    assert query_params[3] == "kpi"
    assert query_params[4] == "kpi-999"
    # Ensure JSON serializations match
    assert json.loads(query_params[5]) == {"value": 10}
    assert query_params[6] == "127.0.0.1"
    assert json.loads(query_params[7]) == {"source": "api"}
    
    mock_conn.commit.assert_called_once()


# ---------------------------------------------------------
# Test Compliance Logging
# ---------------------------------------------------------
@patch("backend.audit.compliance_engine.get_tenant_id")
@patch("backend.audit.compliance_engine.get_connection")
def test_record_compliance_event(mock_get_conn, mock_get_tenant_id):
    mock_get_tenant_id.return_value = "tenant-xyz"
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    record_compliance_event(
        event_type="SOC2_CHECK",
        status="compliant",
        details={"scope": "access_control"}
    )

    mock_cursor.execute.assert_called_once()
    args, _ = mock_cursor.execute.call_args
    query_str = args[0]
    query_params = args[1]

    assert "INSERT INTO compliance_events" in query_str
    assert query_params[0] == "tenant-xyz"
    assert query_params[1] == "SOC2_CHECK"
    assert query_params[2] == "compliant"
    assert query_params[3] == {"scope": "access_control"}
    
    mock_conn.commit.assert_called_once()


# ---------------------------------------------------------
# Test Audit Event Queries
# ---------------------------------------------------------
@patch("backend.audit.audit_queries.get_connection")
def test_get_audit_events(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("log-1", "user-1", "action-1", "res-type", "res-id", "{}", "127.0.0.1", "{}", None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    events = get_audit_events("tenant-1", limit=10, offset=0)
    assert len(events) == 1
    assert events[0][0] == "log-1"
    mock_cursor.execute.assert_called_once()


@patch("backend.audit.audit_queries.get_connection")
def test_get_compliance_events(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("comp-1", "SOC2", "compliant", {}, None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    events = get_compliance_events("tenant-1", limit=5, offset=1)
    assert len(events) == 1
    assert events[0][0] == "comp-1"
    mock_cursor.execute.assert_called_once()
