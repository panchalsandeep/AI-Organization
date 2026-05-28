from backend.embeddings.generate_embeddings import generate_embedding
from backend.database.supabase_client import get_supabase_client

def ingest_memory(
    title,
    content,
    content_type,
    source,
    tags,
    metadata
):
    embedding = generate_embedding(content)
    supabase = get_supabase_client()

    response = supabase.table("operational_memory").insert({
        "title": title,
        "content": content,
        "content_type": content_type,
        "source": source,
        "tags": tags,
        "metadata": metadata,
        "embedding": embedding
    }).execute()

    return response