import uuid

from backend.database.supabase_client import get_supabase_client
from backend.ingestion.ingest_memory import ingest_memory


def _cleanup_test_row(title: str):
    client = get_supabase_client()
    client.table("operational_memory").delete().match({"title": title}).execute()


def test_insert_memory_returns_response():
    title = f"Direct Insert Test - {uuid.uuid4()}"
    try:
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
    finally:
        _cleanup_test_row(title)
