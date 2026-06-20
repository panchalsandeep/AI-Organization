-- Migration: Predictive Analytics Index
CREATE INDEX IF NOT EXISTS idx_kpi_metrics_forecast ON kpi_metrics (kpi_id, timestamp ASC);
