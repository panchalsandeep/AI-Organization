-- Migration: KPI Engine Schema
CREATE TABLE IF NOT EXISTS kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    kpi_type TEXT NOT NULL, -- 'number', 'percentage', 'currency'
    formula TEXT, -- Formula string if dynamic
    target_value NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS kpi_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    kpi_id UUID NOT NULL REFERENCES kpis(id) ON DELETE CASCADE,
    value NUMERIC NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Index for performance on time-series queries
CREATE INDEX IF NOT EXISTS idx_kpi_metrics_tenant_kpi_time ON kpi_metrics (tenant_id, kpi_id, timestamp DESC);
