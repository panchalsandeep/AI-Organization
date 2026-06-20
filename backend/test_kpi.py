import pytest
from unittest.mock import patch, MagicMock
from backend.kpi.kpi_engine import create_kpi, list_kpis, log_kpi_metric, get_kpi_history
from backend.kpi.aggregation import aggregate_kpi_metrics
from backend.kpi.realtime_service import manager as kpi_manager

@patch("backend.kpi.kpi_engine.get_connection")
def test_create_kpi(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = create_kpi("t-1", "Revenue", "currency", target_value=1000.0)
    assert res["name"] == "Revenue"
    assert res["target_value"] == 1000.0
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch("backend.kpi.kpi_engine.get_connection")
def test_list_kpis(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("k-1", "Conversion Rate", "percentage", None, 0.05, None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = list_kpis("t-1")
    assert len(res) == 1
    assert res[0]["name"] == "Conversion Rate"
    assert res[0]["target_value"] == 0.05

@patch("backend.kpi.kpi_engine.get_connection")
def test_log_kpi_metric(mock_get_conn):
    mock_cursor = MagicMock()
    # Mock finding target_value for alert checks
    mock_cursor.fetchone.return_value = (100.0, "Active Users")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    # Log 90.0 (less than 100.0) -> triggers alert
    res = log_kpi_metric("t-1", "k-1", 90.0)
    assert res["value"] == 90.0
    assert res["alert_triggered"] is True
    assert mock_cursor.execute.call_count == 2
    mock_conn.commit.assert_called_once()

@patch("backend.kpi.kpi_engine.get_connection")
def test_get_kpi_history(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("m-1", 10.5, None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = get_kpi_history("t-1", "k-1", limit=10)
    assert len(res) == 1
    assert res[0]["value"] == 10.5

@patch("backend.kpi.aggregation.get_connection")
def test_aggregate_kpi_metrics(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("2026-06-20", 50.0, 100.0, 2)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = aggregate_kpi_metrics("t-1", "k-1", interval="day")
    assert len(res) == 1
    assert res[0]["avg_value"] == 50.0
    assert res[0]["count"] == 2
