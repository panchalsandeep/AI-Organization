-- Migration: Decision Intelligence Portal
CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    context TEXT,
    alternatives JSONB DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'proposed',
    estimated_impact INTEGER NOT NULL CHECK (estimated_impact BETWEEN 1 AND 5),
    actual_impact INTEGER CHECK (actual_impact BETWEEN 1 AND 5),
    outcome TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    decided_at TIMESTAMP WITH TIME ZONE
);
