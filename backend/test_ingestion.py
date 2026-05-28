import uuid

from backend.database.supabase_client import get_supabase_client
from backend.ingestion.ingest_memory import ingest_memory


def _cleanup_test_row(title: str):
    client = get_supabase_client()
    client.table("operational_memory").delete().match({"title": title}).execute()


def test_ingest_memory_returns_response():
    title = f"AI Operations Vision - {uuid.uuid4()}"
    try:
        response = ingest_memory(
            title=title,
            content="""
            Build a centralized AI-first company operating system
            with operational memory, AI agents, automation,
            semantic retrieval, KPI orchestration,
            and closed-loop intelligence workflows.
            """,
            content_type="strategy",
            source="founder",
            tags=["ai", "operations", "strategy"],
            metadata={
                "department": "leadership",
                "priority": "high"
            }
        )

        assert hasattr(response, "data")
        assert response.data is not None
        assert isinstance(response.data, list)
    finally:
        _cleanup_test_row(title)
