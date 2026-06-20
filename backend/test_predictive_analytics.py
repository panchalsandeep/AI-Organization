import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from backend.analytics.predictive_engine import (
    calculate_forecast,
    detect_anomalies,
    parse_iso_timestamp
)
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.auth.authentication import create_access_token

client = TestClient(app)

def get_auth_headers(permissions):
    token = create_access_token({"sub": "test-user-id", "permissions": permissions})
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "test-tenant-id",
        "X-Tenant-Name": "Test Tenant"
    }

def test_parse_iso_timestamp():
    dt = datetime(2026, 6, 20, 12, 0, 0)
    assert parse_iso_timestamp(dt) == dt
    assert parse_iso_timestamp("2026-06-20T12:00:00Z").year == 2026
    assert parse_iso_timestamp("invalid").year == datetime.utcnow().year


def test_calculate_forecast_insufficient_points():
    assert calculate_forecast([]) == []
    assert calculate_forecast([{"value": 10, "timestamp": "2026-06-20"}]) == []


def test_calculate_forecast_linear_trend():
    now = datetime(2026, 6, 20, 12, 0, 0)
    metrics = [
        {"value": 10, "timestamp": (now - timedelta(days=2)).isoformat()},
        {"value": 12, "timestamp": (now - timedelta(days=1)).isoformat()},
        {"value": 14, "timestamp": now.isoformat()}
    ]

    forecast = calculate_forecast(metrics, steps=3)
    assert len(forecast) == 3
    # Next values should be 16, 18, 20
    assert abs(forecast[0]["value"] - 16) < 0.01
    assert abs(forecast[1]["value"] - 18) < 0.01
    assert abs(forecast[2]["value"] - 20) < 0.01
    assert forecast[0]["confidence_upper"] > forecast[0]["value"]
    assert forecast[0]["confidence_lower"] < forecast[0]["value"]


def test_detect_anomalies():
    now = datetime(2026, 6, 20, 12, 0, 0)
    # A set of normal metrics plus one outlier
    metrics = [
        {"id": "m-1", "value": 10, "timestamp": (now - timedelta(days=4)).isoformat()},
        {"id": "m-2", "value": 11, "timestamp": (now - timedelta(days=3)).isoformat()},
        {"id": "m-3", "value": 10, "timestamp": (now - timedelta(days=2)).isoformat()},
        {"id": "m-4", "value": 12, "timestamp": (now - timedelta(days=1)).isoformat()},
        {"id": "m-5", "value": 100, "timestamp": now.isoformat()} # Outlier!
    ]

    anomalies = detect_anomalies(metrics, threshold=1.5)
    assert len(anomalies) == 1
    assert anomalies[0]["id"] == "m-5"
    assert anomalies[0]["value"] == 100.0
    assert anomalies[0]["z_score"] > 1.5


@patch("backend.api.main.get_kpi_history")
def test_forecast_api_route(mock_history):
    now = datetime(2026, 6, 20, 12, 0, 0)
    mock_history.return_value = [
        {"value": 10, "timestamp": (now - timedelta(days=2)).isoformat()},
        {"value": 12, "timestamp": (now - timedelta(days=1)).isoformat()},
        {"value": 14, "timestamp": now.isoformat()}
    ]

    headers = get_auth_headers(["kpi:read"])
    response = client.get("/kpi/k-1/forecast?steps=2", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["forecast"]) == 2


@patch("backend.api.main.get_kpi_history")
def test_anomalies_api_route(mock_history):
    now = datetime(2026, 6, 20, 12, 0, 0)
    mock_history.return_value = [
        {"value": 10, "timestamp": (now - timedelta(days=4)).isoformat()},
        {"value": 11, "timestamp": (now - timedelta(days=3)).isoformat()},
        {"value": 10, "timestamp": (now - timedelta(days=2)).isoformat()},
        {"value": 12, "timestamp": (now - timedelta(days=1)).isoformat()},
        {"value": 100, "timestamp": now.isoformat()}
    ]

    headers = get_auth_headers(["kpi:read"])
    response = client.get("/kpi/k-1/anomalies?threshold=1.5", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["anomalies"]) == 1


@patch("backend.api.main.log_kpi_metric")
@patch("backend.api.main.get_kpi_history")
@patch("backend.api.main.log_audit_event")
@patch("backend.api.main.kpi_manager.broadcast_to_tenant")
def test_metric_logging_triggers_anomaly(mock_broadcast, mock_audit, mock_history, mock_log_metric):
    mock_log_metric.return_value = {"id": "m-new", "alert_triggered": False}
    now = datetime(2026, 6, 20, 12, 0, 0)
    mock_history.return_value = [
        {"id": f"m-{i}", "value": 10, "timestamp": (now - timedelta(days=10-i)).isoformat()}
        for i in range(1, 10)
    ] + [{"id": "m-new", "value": 100, "timestamp": now.isoformat()}]

    headers = get_auth_headers(["kpi:write"])
    response = client.post("/kpi/metric", json={"kpi_id": "k-1", "value": 100.0}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_audit.assert_called_once()
    mock_broadcast.assert_called_once()
    broadcast_msg = mock_broadcast.call_args[1]["message"]
    assert broadcast_msg["anomaly_flagged"] is True
    assert broadcast_msg["z_score"] > 1.5
