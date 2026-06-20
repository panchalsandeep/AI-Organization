import pytest
from unittest.mock import patch, MagicMock
from backend.meeting_intelligence.transcription_service import transcribe_audio
from backend.meeting_intelligence.action_extractor import extract_action_items
from backend.meeting_intelligence.summary_generator import generate_meeting_summary
from backend.meeting_intelligence.models import create_meeting, get_meeting, list_meetings

@patch("backend.meeting_intelligence.transcription_service.SecretsManager.get_openai_api_key")
def test_transcribe_audio_fallback(mock_get_key):
    mock_get_key.return_value = None
    # Test fallback behavior when API key is missing
    res = transcribe_audio("nonexistent_file.wav")
    assert "[Mock Transcript]" in res

@patch("backend.meeting_intelligence.transcription_service.SecretsManager.get_openai_api_key")
@patch("backend.meeting_intelligence.transcription_service.OpenAI")
@patch("backend.meeting_intelligence.transcription_service.os.path.exists")
def test_transcribe_audio_openai(mock_exists, mock_openai, mock_get_key):
    mock_get_key.return_value = "secret-key"
    mock_exists.return_value = True
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value.text = "Hello team"
    mock_openai.return_value = mock_client

    # Mock open
    with patch("builtins.open", MagicMock()):
        res = transcribe_audio("some_file.wav")
        assert res == "Hello team"

@patch("backend.meeting_intelligence.action_extractor.SecretsManager.get_openai_api_key")
def test_extract_action_items_fallback(mock_get_key):
    mock_get_key.return_value = None
    res = extract_action_items("some transcript")
    assert isinstance(res, list)
    assert len(res) > 0
    assert "task" in res[0]

@patch("backend.meeting_intelligence.summary_generator.SecretsManager.get_openai_api_key")
def test_generate_meeting_summary_fallback(mock_get_key):
    mock_get_key.return_value = None
    res = generate_meeting_summary("some transcript")
    assert "roadmap" in res or "Sprint" in res

@patch("backend.meeting_intelligence.models.get_connection")
def test_create_meeting(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = create_meeting("t-1", "Weekly sync", 100, "hello", "summary text", [{"task": "t"}], "url")
    assert res["title"] == "Weekly sync"
    assert res["audio_url"] == "url"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

@patch("backend.meeting_intelligence.models.get_connection")
def test_get_meeting(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("m-1", "t-1", "Weekly sync", None, 100, "hello", "summary text", '[{"task": "t"}]', "url")
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = get_meeting("m-1")
    assert res is not None
    assert res["title"] == "Weekly sync"
    assert res["action_items"] == [{"task": "t"}]

@patch("backend.meeting_intelligence.models.get_connection")
def test_list_meetings(mock_get_conn):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("m-1", "Weekly sync", None, 100, "summary text", "url")
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = list_meetings("t-1")
    assert len(res) == 1
    assert res[0]["title"] == "Weekly sync"
