from typing import Callable
from fastapi import Depends
from backend.auth.authentication import require_permission


def require_permission_decorator(permission: str):
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            await Depends(require_permission(permission))
            return await func(*args, **kwargs)
        return wrapper
    return decorator
