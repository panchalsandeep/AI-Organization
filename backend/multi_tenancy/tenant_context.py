from contextvars import ContextVar
from typing import Optional

_tenant_id: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
_tenant_name: ContextVar[Optional[str]] = ContextVar("tenant_name", default=None)


def set_tenant_context(tenant_id: str, tenant_name: str) -> None:
    _tenant_id.set(tenant_id)
    _tenant_name.set(tenant_name)


def get_tenant_id() -> Optional[str]:
    return _tenant_id.get()


def get_tenant_name() -> Optional[str]:
    return _tenant_name.get()


def clear_tenant_context() -> None:
    _tenant_id.set(None)
    _tenant_name.set(None)
