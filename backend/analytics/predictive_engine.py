import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

def parse_iso_timestamp(ts: Any) -> datetime:
    if isinstance(ts, datetime):
        return ts
    try:
        # Strip Z or +offset for parsing if needed
        clean_ts = str(ts).replace("Z", "+00:00")
        return datetime.fromisoformat(clean_ts)
    except Exception:
        return datetime.utcnow()

def calculate_forecast(metrics: List[Dict[str, Any]], steps: int = 5) -> List[Dict[str, Any]]:
    """
    Calculate future KPI values using least-squares linear regression
    with standard error prediction intervals.
    """
    if len(metrics) < 3:
        return []

    # Sort metrics chronologically
    sorted_metrics = sorted(metrics, key=lambda m: parse_iso_timestamp(m["timestamp"]))
    n = len(sorted_metrics)
    
    # Convert timestamps to numeric indices (x) and get values (y)
    x = list(range(n))
    y = [float(m["value"]) for m in sorted_metrics]
    
    # Calculate means
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    # Calculate slope (m) and intercept (c)
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    if denominator == 0:
        slope = 0.0
        intercept = mean_y
    else:
        slope = numerator / denominator
        intercept = mean_y - slope * mean_x
        
    # Calculate standard error of residuals
    residual_sum_of_squares = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
    if n > 2:
        std_error = math.sqrt(residual_sum_of_squares / (n - 2))
    else:
        std_error = 0.0
        
    if std_error == 0.0:
        std_error = 0.05 * (mean_y if mean_y != 0 else 1.0)

    # Estimate average interval delta (in seconds) between metrics
    deltas = []
    for i in range(1, n):
        t1 = parse_iso_timestamp(sorted_metrics[i-1]["timestamp"])
        t2 = parse_iso_timestamp(sorted_metrics[i]["timestamp"])
        deltas.append((t2 - t1).total_seconds())
        
    avg_delta_seconds = sum(deltas) / len(deltas) if deltas else 86400.0 # Default to 1 day
    if avg_delta_seconds <= 0:
        avg_delta_seconds = 86400.0
        
    last_timestamp = parse_iso_timestamp(sorted_metrics[-1]["timestamp"])
    
    forecast_results = []
    for j in range(1, steps + 1):
        future_x = (n - 1) + j
        predicted_val = slope * future_x + intercept
        
        # Prediction interval width increases as we project further out
        interval_width = 1.96 * std_error * math.sqrt(1 + (1 / n) + (j / n))
        
        future_time = last_timestamp + timedelta(seconds=avg_delta_seconds * j)
        
        forecast_results.append({
            "timestamp": future_time.isoformat(),
            "value": round(predicted_val, 4),
            "confidence_upper": round(predicted_val + interval_width, 4),
            "confidence_lower": round(predicted_val - interval_width, 4)
        })
        
    return forecast_results

def detect_anomalies(metrics: List[Dict[str, Any]], threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detect statistical anomalies in KPI metrics using Z-score thresholding.
    """
    if len(metrics) < 3:
        return []

    values = [float(m["value"]) for m in metrics]
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std_dev = math.sqrt(variance)
    
    if std_dev == 0.0:
        return []
        
    anomalies = []
    for m in metrics:
        val = float(m["value"])
        z_score = (val - mean) / std_dev
        if abs(z_score) > threshold:
            anomalies.append({
                "id": m.get("id"),
                "timestamp": parse_iso_timestamp(m["timestamp"]).isoformat(),
                "value": val,
                "z_score": round(z_score, 2),
                "threshold": threshold
            })
            
    return anomalies
