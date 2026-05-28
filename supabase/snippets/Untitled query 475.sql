create or replace function match_operational_memory (
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id uuid,
  title text,
  content text,
  content_type text,
  source text,
  tags text[],
  metadata jsonb,
  similarity float
)
language sql
as $$
  select
    operational_memory.id,
    operational_memory.title,
    operational_memory.content,
    operational_memory.content_type,
    operational_memory.source,
    operational_memory.tags,
    operational_memory.metadata,
    1 - (operational_memory.embedding <=> query_embedding) as similarity
  from operational_memory
  order by operational_memory.embedding <=> query_embedding
  limit match_count;
$$;