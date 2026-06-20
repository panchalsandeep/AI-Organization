from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.multi_tenancy.tenant_context import set_tenant_context


class TenantRouterMiddleware(BaseHTTPMiddleware):
    """Middleware to route requests to the correct tenant context."""

    async def dispatch(self, request: Request, call_next):
        exempt_paths = ["/", "/health", "/auth/token", "/admin/tenant", "/admin/tenants"]
        if request.url.path in exempt_paths or request.url.path.startswith("/static") or request.url.path.startswith("/admin/tenant"):
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-ID")
        tenant_name = request.headers.get("X-Tenant-Name", "")

        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing X-Tenant-ID header"}
            )

        set_tenant_context(tenant_id, tenant_name)
        response = await call_next(request)
        return response
