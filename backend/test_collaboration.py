import pytest
from unittest.mock import patch, MagicMock
from backend.collaboration.chat_service import save_chat_message, get_chat_history, chat_manager
from backend.collaboration.comment_service import create_comment, get_comments_for_resource

@patch("backend.collaboration.chat_service.get_connection")
def test_save_chat_message(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = save_chat_message("t-1", "room-1", "user-1", "Alice", "Hello world")
    assert res["sender_name"] == "Alice"
    assert res["message_text"] == "Hello world"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch("backend.collaboration.chat_service.get_connection")
def test_get_chat_history(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("msg-1", "user-1", "Alice", "Hello world", None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = get_chat_history("t-1", "room-1")
    assert len(res) == 1
    assert res[0]["sender_name"] == "Alice"
    assert res[0]["message_text"] == "Hello world"

@patch("backend.collaboration.comment_service.get_connection")
def test_create_comment(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = create_comment("t-1", "kpi", "k-1", "user-1", "Alice", "Nice chart", parent_comment_id="p-1")
    assert res["sender_name"] == "Alice"
    assert res["comment_text"] == "Nice chart"
    assert res["parent_comment_id"] == "p-1"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch("backend.collaboration.comment_service.get_connection")
def test_get_comments_for_resource(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("c-1", "p-1", "user-1", "Alice", "Nice chart", None)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = get_comments_for_resource("t-1", "kpi", "k-1")
    assert len(res) == 1
    assert res[0]["sender_name"] == "Alice"
    assert res[0]["parent_comment_id"] == "p-1"
