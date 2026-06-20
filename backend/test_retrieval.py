from unittest.mock import patch, MagicMock
from backend.retrieval.search_memory import search_memory

@patch("backend.retrieval.search_memory.generate_embedding")
@patch("backend.retrieval.search_memory.get_supabase_client")
def test_search_memory_returns_results(mock_get_supabase, mock_generate_embedding):
    mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
    
    mock_response = MagicMock()
    mock_response.data = [
        {
            "title": "AI operating system strategy",
            "content": "Centralized company operating system",
            "metadata": {"dept": "strategy"},
            "embedding": [0.11, 0.19, 0.32]
        },
        {
            "title": "Unrelated topic",
            "content": "Some other text content",
            "metadata": {"dept": "other"},
            "embedding": [0.9, -0.1, 0.0]
        }
    ]
    
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.execute.return_value = mock_response
    mock_get_supabase.return_value = mock_client
    
    results = search_memory("AI operating system strategy")

    assert isinstance(results, list)
    assert len(results) > 0
    assert "content" in results[0]
    assert "similarity" in results[0]
    assert results[0]["title"] == "AI operating system strategy"
    assert results[0]["similarity"] > results[1]["similarity"]
    
    mock_generate_embedding.assert_called_once_with("AI operating system strategy")
    mock_client.table.assert_called_once_with("operational_memory")
