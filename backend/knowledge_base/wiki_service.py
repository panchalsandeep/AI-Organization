import uuid
import re
from typing import Dict, Any, List, Optional
from backend.database.postgres_client import get_connection
from backend.ingestion.ingest_memory import ingest_memory
from backend.database.supabase_client import get_supabase_client

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text or "untitled"

def sync_wiki_to_memory(tenant_id: str, page_id: str, title: str, content: str, tags: List[str]):
    """Sync wiki page text and metadata to operational_memory for vector indexing."""
    try:
        supabase = get_supabase_client()
        # Delete existing vector index for this wiki page to prevent duplicates
        supabase.table("operational_memory").delete().filter("metadata->>wiki_page_id", "eq", page_id).execute()
        
        # Ingest new embedding index
        ingest_memory(
            title=title,
            content=content,
            content_type="wiki",
            source="wiki",
            tags=tags,
            metadata={
                "tenant_id": tenant_id,
                "wiki_page_id": page_id
            }
        )
    except Exception as e:
        # Avoid crashing service if vector indexing fails
        print(f"Error syncing wiki page {page_id} to vector memory: {e}")

def delete_wiki_from_memory(page_id: str):
    """Remove wiki page index from operational_memory."""
    try:
        supabase = get_supabase_client()
        supabase.table("operational_memory").delete().filter("metadata->>wiki_page_id", "eq", page_id).execute()
    except Exception as e:
        print(f"Error deleting wiki page {page_id} from vector memory: {e}")

def create_wiki_page(
    tenant_id: str,
    title: str,
    slug: Optional[str],
    content: str,
    tags: List[str],
    created_by: str
) -> Dict[str, Any]:
    page_slug = slugify(slug or title)
    page_id = str(uuid.uuid4())
    
    conn = get_connection()
    with conn.cursor() as cur:
        # Check slug uniqueness for this tenant. If slug already exists, append a unique suffix
        cur.execute("SELECT id FROM wiki_pages WHERE tenant_id = %s AND slug = %s", (tenant_id, page_slug))
        if cur.fetchone():
            page_slug = f"{page_slug}-{page_id[:8]}"
            
        cur.execute(
            "INSERT INTO wiki_pages (id, tenant_id, title, slug, content, tags, version, created_by, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, 1, %s, NOW(), NOW())",
            (page_id, tenant_id, title, page_slug, content, tags, created_by)
        )
        cur.execute(
            "INSERT INTO wiki_versions (id, wiki_page_id, tenant_id, title, content, version, updated_by, created_at) "
            "VALUES (%s, %s, %s, %s, %s, 1, %s, NOW())",
            (str(uuid.uuid4()), page_id, tenant_id, title, content, created_by)
        )
        conn.commit()
        
    # Trigger background sync to operational memory
    sync_wiki_to_memory(tenant_id, page_id, title, content, tags)
    
    return {
        "id": page_id,
        "tenant_id": tenant_id,
        "title": title,
        "slug": page_slug,
        "content": content,
        "tags": tags,
        "version": 1,
        "created_by": created_by
    }

def list_wiki_pages(tenant_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, slug, content, tags, version, created_by, created_at, updated_at "
            "FROM wiki_pages WHERE tenant_id = %s ORDER BY title ASC",
            (tenant_id,)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "slug": row[2],
                "content": row[3],
                "tags": row[4] if row[4] else [],
                "version": row[5],
                "created_by": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "updated_at": row[8].isoformat() if row[8] else None
            }
            for row in rows
        ]

def get_wiki_page(tenant_id: str, page_id_or_slug: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        # Check if argument is a UUID structure
        is_uuid = False
        try:
            uuid.UUID(page_id_or_slug)
            is_uuid = True
        except ValueError:
            pass
            
        if is_uuid:
            cur.execute(
                "SELECT id, title, slug, content, tags, version, created_by, created_at, updated_at "
                "FROM wiki_pages WHERE tenant_id = %s AND id = %s",
                (tenant_id, page_id_or_slug)
            )
        else:
            cur.execute(
                "SELECT id, title, slug, content, tags, version, created_by, created_at, updated_at "
                "FROM wiki_pages WHERE tenant_id = %s AND slug = %s",
                (tenant_id, page_id_or_slug)
            )
            
        row = cur.fetchone()
        if not row:
            return None
            
        return {
            "id": row[0],
            "title": row[1],
            "slug": row[2],
            "content": row[3],
            "tags": row[4] if row[4] else [],
            "version": row[5],
            "created_by": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "updated_at": row[8].isoformat() if row[8] else None
        }

def update_wiki_page(
    tenant_id: str,
    page_id: str,
    title: str,
    slug: Optional[str],
    content: str,
    tags: List[str],
    updated_by: str
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM wiki_pages WHERE tenant_id = %s AND id = %s", (tenant_id, page_id))
        row = cur.fetchone()
        if not row:
            return None
            
        current_version = row[0]
        new_version = current_version + 1
        page_slug = slugify(slug or title)
        
        # Verify slug uniqueness if slug changed
        cur.execute("SELECT id FROM wiki_pages WHERE tenant_id = %s AND slug = %s AND id != %s", (tenant_id, page_slug, page_id))
        if cur.fetchone():
            page_slug = f"{page_slug}-{page_id[:8]}"
            
        cur.execute(
            "UPDATE wiki_pages "
            "SET title = %s, slug = %s, content = %s, tags = %s, version = %s, updated_at = NOW() "
            "WHERE tenant_id = %s AND id = %s",
            (title, page_slug, content, tags, new_version, tenant_id, page_id)
        )
        
        cur.execute(
            "INSERT INTO wiki_versions (id, wiki_page_id, tenant_id, title, content, version, updated_by, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
            (str(uuid.uuid4()), page_id, tenant_id, title, content, new_version, updated_by)
        )
        conn.commit()
        
    sync_wiki_to_memory(tenant_id, page_id, title, content, tags)
    
    return get_wiki_page(tenant_id, page_id)

def delete_wiki_page(tenant_id: str, page_id: str) -> bool:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM wiki_pages WHERE tenant_id = %s AND id = %s", (tenant_id, page_id))
        deleted = cur.rowcount > 0
        conn.commit()
        
    if deleted:
        delete_wiki_from_memory(page_id)
        
    return deleted

def get_wiki_page_history(tenant_id: str, page_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, content, version, updated_by, created_at "
            "FROM wiki_versions WHERE tenant_id = %s AND wiki_page_id = %s ORDER BY version DESC",
            (tenant_id, page_id)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "version": row[3],
                "updated_by": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            }
            for row in rows
        ]

def search_wiki_text(tenant_id: str, query: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    like_pattern = f"%{query}%"
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, slug, content, tags, version, created_by, created_at, updated_at "
            "FROM wiki_pages "
            "WHERE tenant_id = %s AND (title ILIKE %s OR content ILIKE %s OR %s = ANY(tags)) "
            "ORDER BY title ASC",
            (tenant_id, like_pattern, like_pattern, query)
        )
        rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "slug": row[2],
                "content": row[3],
                "tags": row[4] if row[4] else [],
                "version": row[5],
                "created_by": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "updated_at": row[8].isoformat() if row[8] else None
            }
            for row in rows
        ]
