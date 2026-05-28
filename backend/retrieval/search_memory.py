import ast
import math
from backend.embeddings.generate_embeddings import generate_embedding
from backend.database.supabase_client import get_supabase_client


def _parse_embedding(value):
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return []
    if isinstance(value, list):
        return value
    return list(value)


def _cosine_similarity(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_memory(query, match_count=5):
    query_embedding = generate_embedding(query)
    client = get_supabase_client()

    response = client.table('operational_memory').select('title,content,metadata,embedding').execute()
    rows = response.data or []

    scored = []
    for row in rows:
        embedding = _parse_embedding(row.get('embedding'))
        similarity = _cosine_similarity(query_embedding, embedding)
        scored.append({
            'title': row.get('title'),
            'content': row.get('content'),
            'metadata': row.get('metadata'),
            'similarity': similarity,
        })

    scored.sort(key=lambda item: item['similarity'], reverse=True)
    return scored[:match_count]