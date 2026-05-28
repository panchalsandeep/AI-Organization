create table operational_memory (
    id uuid primary key default gen_random_uuid(),
    title text,
    content text,
    content_type text,
    source text,
    tags text[],
    metadata jsonb,
    embedding vector(1536),
    created_at timestamp default now()
);