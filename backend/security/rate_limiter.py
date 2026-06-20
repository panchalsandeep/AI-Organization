import time
from fastapi import HTTPException, status

_rate_limits = {}


def rate_limit(key: str, limit: int = 100, window_seconds: int = 60):
    now = time.time()
    window_start = now - window_seconds
    if key not in _rate_limits:
        _rate_limits[key] = []
    _rate_limits[key] = [timestamp for timestamp in _rate_limits[key] if timestamp > window_start]
    if len(_rate_limits[key]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    _rate_limits[key].append(now)
