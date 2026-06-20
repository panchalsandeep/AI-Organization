import pytest
from unittest.mock import patch, MagicMock
import datetime
from backend.decision_intelligence.decision_service import (
    create_decision,
    list_decisions,
    get_decision,
    update_decision,
    delete_decision
)

@patch("backend.decision_intelligence.decision_service.get_connection")
def test_create_decision(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = create_decision(
        tenant_id="t-1",
        title="Test Title",
        description="Test Desc",
        context="Test Context",
        alternatives=["Alt A", "Alt B"],
        status="proposed",
        estimated_impact=4,
        created_by="admin"
    )

    assert res["title"] == "Test Title"
    assert res["status"] == "proposed"
    assert res["estimated_impact"] == 4
    assert res["alternatives"] == ["Alt A", "Alt B"]
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("backend.decision_intelligence.decision_service.get_connection")
def test_list_decisions(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchall.return_value = [
        ("id-1", "T1", "D1", "C1", '["A", "B"]', "proposed", 4, None, None, "admin", now_dt, now_dt, None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = list_decisions("t-1")
    assert len(res) == 1
    assert res[0]["id"] == "id-1"
    assert res[0]["title"] == "T1"
    assert res[0]["alternatives"] == ["A", "B"]


@patch("backend.decision_intelligence.decision_service.get_connection")
def test_get_decision_found(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchone.return_value = ("id-1", "T1", "D1", "C1", '["A"]', "decided", 3, 4, "Outcome details", "admin", now_dt, now_dt, now_dt)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = get_decision("t-1", "id-1")
    assert res is not None
    assert res["id"] == "id-1"
    assert res["status"] == "decided"
    assert res["actual_impact"] == 4
    assert res["outcome"] == "Outcome details"


@patch("backend.decision_intelligence.decision_service.get_connection")
def test_get_decision_not_found(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = get_decision("t-1", "missing")
    assert res is None


@patch("backend.decision_intelligence.decision_service.get_connection")
def test_update_decision_not_found(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = update_decision("t-1", "missing", "T", "D", None, [], "proposed", 3, None, None)
    assert res is None


@patch("backend.decision_intelligence.decision_service.get_connection")
def test_update_decision_success(mock_get_conn):
    mock_cursor = MagicMock()
    # Check returns existing, then fetch retrieves the updated record
    mock_cursor.fetchone.side_effect = [
        ("id-1",), # Exists check
        ("id-1", "T-Updated", "D-Updated", "C", '[]', "evaluated", 3, 3, "Outcome text", "admin", None, None, None) # Return updated detail
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = update_decision("t-1", "id-1", "T-Updated", "D-Updated", "C", [], "evaluated", 3, 3, "Outcome text")
    assert res is not None
    assert res["title"] == "T-Updated"
    assert res["status"] == "evaluated"
    assert res["actual_impact"] == 3
    assert res["outcome"] == "Outcome text"
    mock_conn.commit.assert_called_once()


@patch("backend.decision_intelligence.decision_service.get_connection")
def test_delete_decision(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    success = delete_decision("t-1", "id-1")
    assert success is True
    mock_conn.commit.assert_called_once()
