-- Enable pgvector extension
create extension if not exists vector;

-- Documents table
create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    title text unique not null,
    source_type text not null check (source_type in ('regulation', 'user_upload')),
    regulation_code text,
    created_at timestamptz default now()
);

-- Chunks table with embeddings (Gemini embedding-001 @ 1024 dims via MRL)
create table if not exists chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references documents(id) on delete cascade,
    content text not null,
    chunk_index int not null,
    article_ref text,
    token_count int not null,
    embedding vector(1024) not null
);

create index if not exists chunks_document_id_idx on chunks(document_id);

-- HNSW index for cosine similarity search
create index if not exists chunks_embedding_hnsw_idx
    on chunks using hnsw (embedding vector_cosine_ops);

-- Similarity search function
create or replace function match_chunks(
    query_embedding vector(1024),
    match_count int,
    filter_regulation text default null
)
returns table (
    content text,
    article_ref text,
    regulation_code text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        c.content,
        c.article_ref,
        d.regulation_code,
        1 - (c.embedding <=> query_embedding) as similarity
    from chunks c
    join documents d on d.id = c.document_id
    where filter_regulation is null
       or d.regulation_code = filter_regulation
    order by c.embedding <=> query_embedding
    limit match_count;
end;
$$;
