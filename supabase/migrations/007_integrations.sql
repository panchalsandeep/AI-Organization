-- Migration: Integrations and Sync Logs
CREATE TABLE IF NOT EXISTS integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    integration_type TEXT NOT NULL, -- 'slack', 'notion', 'google_drive', 'github'
    config JSONB DEFAULT '{}', -- Encrypted tokens/configurations
    status TEXT NOT NULL DEFAULT 'disconnected', -- 'connected', 'disconnected', 'error'
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    records_synced INTEGER DEFAULT 0,
    status TEXT NOT NULL, -- 'success', 'failed'
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_integrations_tenant ON integrations (tenant_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs ON sync_logs (tenant_id, integration_id, timestamp DESC);
