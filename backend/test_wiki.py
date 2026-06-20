import pytest
from unittest.mock import patch, MagicMock
import datetime
from backend.knowledge_base.wiki_service import (
    slugify,
    create_wiki_page,
    list_wiki_pages,
    get_wiki_page,
    update_wiki_page,
    delete_wiki_page,
    get_wiki_page_history,
    search_wiki_text
)

def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("SOC 2 - Compliance guidelines!") == "soc-2-compliance-guidelines"
    assert slugify("---") == "untitled"


@patch("backend.knowledge_base.wiki_service.ingest_memory")
@patch("backend.knowledge_base.wiki_service.get_supabase_client")
@patch("backend.knowledge_base.wiki_service.get_connection")
def test_create_wiki_page(mock_get_conn, mock_get_supabase, mock_ingest_memory):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None # No existing slug conflict
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_supabase_client = MagicMock()
    mock_get_supabase.return_value = mock_supabase_client

    res = create_wiki_page(
        tenant_id="t-1",
        title="Test Wiki Title",
        slug="test-wiki-slug",
        content="Test wiki content text",
        tags=["sec", "ops"],
        created_by="user1"
    )

    assert res["title"] == "Test Wiki Title"
    assert res["slug"] == "test-wiki-slug"
    assert res["content"] == "Test wiki content text"
    assert res["tags"] == ["sec", "ops"]
    assert res["version"] == 1
    assert res["created_by"] == "user1"

    assert mock_cursor.execute.call_count == 3  # Check slug exist + Insert page + Insert version
    mock_conn.commit.assert_called_once()
    mock_ingest_memory.assert_called_once_with(
        title="Test Wiki Title",
        content="Test wiki content text",
        content_type="wiki",
        source="wiki",
        tags=["sec", "ops"],
        metadata={
            "tenant_id": "t-1",
            "wiki_page_id": res["id"]
        }
    )
    mock_supabase_client.table.assert_called_once_with("operational_memory")


@patch("backend.knowledge_base.wiki_service.get_connection")
def test_list_wiki_pages(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchall.return_value = [
        ("id-1", "Wiki Title 1", "wiki-title-1", "Content 1", ["tag1"], 2, "user1", now_dt, now_dt)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = list_wiki_pages("t-1")
    assert len(res) == 1
    assert res[0]["id"] == "id-1"
    assert res[0]["title"] == "Wiki Title 1"
    assert res[0]["tags"] == ["tag1"]
    assert res[0]["version"] == 2


@patch("backend.knowledge_base.wiki_service.get_connection")
def test_get_wiki_page_by_uuid(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchone.return_value = ("id-1", "Wiki Title 1", "wiki-title-1", "Content 1", ["tag1"], 2, "user1", now_dt, now_dt)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    # Valid UUID format triggers UUID check path
    res = get_wiki_page("t-1", "00000000-0000-0000-0000-000000000000")
    assert res is not None
    assert res["id"] == "id-1"
    assert res["slug"] == "wiki-title-1"


@patch("backend.knowledge_base.wiki_service.get_connection")
def test_get_wiki_page_by_slug(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchone.return_value = ("id-1", "Wiki Title 1", "wiki-title-1", "Content 1", ["tag1"], 2, "user1", now_dt, now_dt)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    # Non-UUID format triggers Slug path
    res = get_wiki_page("t-1", "some-article-slug")
    assert res is not None
    assert res["slug"] == "wiki-title-1"


@patch("backend.knowledge_base.wiki_service.sync_wiki_to_memory")
@patch("backend.knowledge_base.wiki_service.get_connection")
def test_update_wiki_page_success(mock_get_conn, mock_sync_memory):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    
    mock_cursor.fetchone.side_effect = [
        (2,),  # Existing version
        None,  # No slug conflict for new slug
        ("id-1", "Wiki Title Updated", "wiki-title-updated", "Content Updated", ["tag1"], 3, "user2", now_dt, now_dt) # fetch result
    ]
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    res = update_wiki_page("t-1", "id-1", "Wiki Title Updated", "wiki-title-updated", "Content Updated", ["tag1"], "user2")
    assert res is not None
    assert res["version"] == 3
    assert res["title"] == "Wiki Title Updated"
    mock_conn.commit.assert_called_once()
    mock_sync_memory.assert_called_once_with("t-1", "id-1", "Wiki Title Updated", "Content Updated", ["tag1"])


@patch("backend.knowledge_base.wiki_service.delete_wiki_from_memory")
@patch("backend.knowledge_base.wiki_service.get_connection")
def test_delete_wiki_page(mock_get_conn, mock_delete_memory):
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    success = delete_wiki_page("t-1", "id-1")
    assert success is True
    mock_conn.commit.assert_called_once()
    mock_delete_memory.assert_called_once_with("id-1")


@patch("backend.knowledge_base.wiki_service.get_connection")
def test_get_wiki_page_history(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchall.return_value = [
        ("v2-id", "Title v2", "Content v2", 2, "user1", now_dt),
        ("v1-id", "Title v1", "Content v1", 1, "user1", now_dt)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    history = get_wiki_page_history("t-1", "id-1")
    assert len(history) == 2
    assert history[0]["version"] == 2
    assert history[1]["version"] == 1


@patch("backend.knowledge_base.wiki_service.get_connection")
def test_search_wiki_text(mock_get_conn):
    mock_cursor = MagicMock()
    now_dt = datetime.datetime.now()
    mock_cursor.fetchall.return_value = [
        ("id-1", "Security Best Practices", "security-best-practices", "Keep passwords safe", ["security"], 1, "admin", now_dt, now_dt)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    results = search_wiki_text("t-1", "Security")
    assert len(results) == 1
    assert results[0]["title"] == "Security Best Practices"
