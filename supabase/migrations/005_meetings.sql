-- Migration: Meeting Intelligence Schema
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    title TEXT NOT NULL,
    date TIMESTAMP WITH TIME ZONE DEFAULT now(),
    duration_seconds INTEGER DEFAULT 0,
    transcript_text TEXT,
    summary TEXT,
    action_items JSONB DEFAULT '[]', -- List of actions
    audio_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index for searching transcripts within tenant contexts
CREATE INDEX IF NOT EXISTS idx_meetings_tenant ON meetings (tenant_id, date DESC);
