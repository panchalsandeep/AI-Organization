import uuid
from unittest.mock import patch, MagicMock
from backend.ingestion.ingest_memory import ingest_memory

@patch("backend.ingestion.ingest_memory.generate_embedding")
@patch("backend.ingestion.ingest_memory.get_supabase_client")
def test_insert_memory_returns_response(mock_get_supabase, mock_generate_embedding):
    mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
    
    mock_response = MagicMock()
    mock_response.data = [{"id": "some-id", "title": "Direct Insert Test"}]
    
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_response
    mock_get_supabase.return_value = mock_client
    
    title = f"Direct Insert Test - {uuid.uuid4()}"
    response = ingest_memory(
        title=title,
        content="Testing operational memory insertion",
        content_type="test",
        source="manual_test",
        tags=["test"],
        metadata={
            "status": "testing"
        }
    )

    assert hasattr(response, "data")
    assert response.data is not None
    assert isinstance(response.data, list)
    assert response.data[0]["title"] == "Direct Insert Test"
    
    mock_generate_embedding.assert_called_once_with("Testing operational memory insertion")
    mock_client.table.assert_called_once_with("operational_memory")
    mock_client.table.return_value.insert.assert_called_once()
