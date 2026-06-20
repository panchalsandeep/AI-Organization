import pytest
from unittest.mock import patch, MagicMock
import datetime
from backend.integrations.connector_factory import (
    ConnectorFactory,
    SlackConnector,
    NotionConnector,
    GoogleDriveConnector,
    GitHubConnector
)
from backend.integrations.sync_manager import (
    create_integration,
    list_integrations,
    test_integration_connection as run_test_integration_connection,
    trigger_sync,
    get_sync_logs
)

# ---------------------------------------------------------
# Test Connectors & Factory
# ---------------------------------------------------------
def test_connector_factory_success():
    slack = ConnectorFactory.get_connector("slack", {"bot_token": "xoxb-123"})
    assert isinstance(slack, SlackConnector)
    assert slack.test_connection() is True

    notion = ConnectorFactory.get_connector("notion", {"api_key": "secret_abc"})
    assert isinstance(notion, NotionConnector)
    assert notion.test_connection() is True

    gdrive = ConnectorFactory.get_connector("google_drive", {"api_key": "key-123"})
    assert isinstance(gdrive, GoogleDriveConnector)
    assert gdrive.test_connection() is True

    github = ConnectorFactory.get_connector("github", {"username": "foo"})
    assert isinstance(github, GitHubConnector)
    assert github.test_connection() is True


def test_connector_factory_invalid_types():
    with pytest.raises(ValueError) as excinfo:
        ConnectorFactory.get_connector("invalid_type", {})
    assert "Unsupported integration type" in str(excinfo.value)


def test_connector_test_connection_failures():
    slack = SlackConnector({"bot_token": "invalid"})
    assert slack.test_connection() is False

    notion = NotionConnector({"api_key": "invalid"})
    assert notion.test_connection() is False

    gdrive = GoogleDriveConnector({})
    assert gdrive.test_connection() is False

    github = GitHubConnector({})
    assert github.test_connection() is False


def test_connector_sync_data():
    slack = SlackConnector({})
    data = slack.sync_data()
    assert len(data) == 2
    assert data[0]["id"] == "msg-slack-1"

    notion = NotionConnector({})
    data = notion.sync_data()
    assert len(data) == 2
    assert data[0]["id"] == "page-notion-1"

    gdrive = GoogleDriveConnector({})
    data = gdrive.sync_data()
    assert len(data) == 2
    assert data[0]["id"] == "drive-file-1"

    github = GitHubConnector({})
    data = github.sync_data()
    assert len(data) == 2
    assert data[0]["id"] == "gh-issue-1"


# ---------------------------------------------------------
# Test Sync Manager
# ---------------------------------------------------------
@patch("backend.integrations.sync_manager.get_connection")
def test_create_integration(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = create_integration(
        tenant_id="tenant-1",
        name="My Slack",
        integration_type="slack",
        config={"bot_token": "xoxb-test"}
      )

    assert res["name"] == "My Slack"
    assert res["integration_type"] == "slack"
    assert res["status"] == "disconnected"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("backend.integrations.sync_manager.get_connection")
def test_list_integrations(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchall.return_value = [
        ("id-1", "My Notion", "notion", "connected", now_dt),
        ("id-2", "My Slack", "slack", "error", None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = list_integrations("tenant-1")
    assert len(res) == 2
    assert res[0]["id"] == "id-1"
    assert res[0]["status"] == "connected"
    assert res[0]["last_sync"] == now_dt.isoformat()
    assert res[1]["last_sync"] is None


@patch("backend.integrations.sync_manager.get_connection")
def test_test_integration_connection(mock_get_conn):
    mock_cursor = MagicMock()
    # To mock test_integration_connection, we fetch integration_type and encrypted_config.
    # We need to simulate the decryption of config. We'll encrypt first using the same internal secret key.
    # Wait, sync_manager has internal global key `_DB_SECRET_KEY` and encrypt_value/decrypt_value.
    from backend.integrations.sync_manager import _DB_SECRET_KEY
    from backend.security.encryption import encrypt_value
    import json
    
    encrypted_conf = encrypt_value(_DB_SECRET_KEY, json.dumps({"bot_token": "xoxb-mock"}))
    mock_cursor.fetchone.return_value = ("slack", encrypted_conf)
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    is_ok = run_test_integration_connection("tenant-1", "id-1")
    assert is_ok is True
    # Verify execute updates the status to 'connected'
    mock_cursor.execute.assert_any_call("UPDATE integrations SET status = %s WHERE id = %s", ("connected", "id-1"))


@patch("backend.integrations.sync_manager.get_connection")
def test_trigger_sync_success(mock_get_conn):
    mock_cursor = MagicMock()
    from backend.integrations.sync_manager import _DB_SECRET_KEY
    from backend.security.encryption import encrypt_value
    import json
    
    encrypted_conf = encrypt_value(_DB_SECRET_KEY, json.dumps({"bot_token": "xoxb-mock"}))
    mock_cursor.fetchone.return_value = ("My Slack", "slack", encrypted_conf)
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = trigger_sync("tenant-1", "id-1")
    assert res["success"] is True
    assert res["records_synced"] == 2
    mock_conn.commit.assert_called_once()


@patch("backend.integrations.sync_manager.get_connection")
def test_trigger_sync_failure(mock_get_conn):
    mock_cursor = MagicMock()
    from backend.integrations.sync_manager import _DB_SECRET_KEY
    from backend.security.encryption import encrypt_value
    import json
    
    # Passing unsupported integration type inside config retrieval to throw connector exception
    encrypted_conf = encrypt_value(_DB_SECRET_KEY, json.dumps({}))
    mock_cursor.fetchone.return_value = ("Broken Conn", "invalid_type", encrypted_conf)
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = trigger_sync("tenant-1", "id-1")
    assert res["success"] is False
    assert "error" in res


@patch("backend.integrations.sync_manager.get_connection")
def test_get_sync_logs(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchall.return_value = [
        ("log-1", 5, "success", None, now_dt)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    logs = get_sync_logs("tenant-1", "id-1")
    assert len(logs) == 1
    assert logs[0]["id"] == "log-1"
    assert logs[0]["records_synced"] == 5
    assert logs[0]["status"] == "success"
