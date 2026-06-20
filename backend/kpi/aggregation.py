from typing import List, Dict, Any
from backend.database.postgres_client import get_connection

def aggregate_kpi_metrics(tenant_id: str, kpi_id: str, interval: str = "day") -> List[Dict[str, Any]]:
    """
    Aggregate metrics by day, hour, or week.
    For local sqlite testing compatibility, we construct simple grouping queries.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        # Group by dynamic date truncation
        # Postgres supports date_trunc, sqlite requires strftime. We'll default to standard postgres format
        trunc_format = "day" if interval not in ["hour", "week"] else interval
        cur.execute(
            f"SELECT date_trunc(%s, timestamp) as time_bucket, AVG(value) as avg_value, SUM(value) as sum_value, COUNT(*) as count_val "
            f"FROM kpi_metrics WHERE tenant_id = %s AND kpi_id = %s "
            f"GROUP BY time_bucket ORDER BY time_bucket ASC",
            (trunc_format, tenant_id, kpi_id)
        )
        rows = cur.fetchall()
        return [
            {
                "time_bucket": row[0].isoformat() if hasattr(row[0], "isoformat") else row[0],
                "avg_value": float(row[1]) if row[1] is not None else 0.0,
                "sum_value": float(row[2]) if row[2] is not None else 0.0,
                "count": row[3]
            }
            for row in rows
        ]
