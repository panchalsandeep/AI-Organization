const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_STORAGE_KEY = "AI_OPS_ADMIN_TOKEN";
const TENANT_STORAGE_KEY = "AI_OPS_TENANT_ID";

function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

function saveToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

function getStoredTenantId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TENANT_STORAGE_KEY);
}

function saveTenantId(tenantId: string) {
  if (typeof window === "undefined") {
    return;
  }
  if (tenantId) {
    window.localStorage.setItem(TENANT_STORAGE_KEY, tenantId);
  } else {
    window.localStorage.removeItem(TENANT_STORAGE_KEY);
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function getTenantHeaders(): Record<string, string> {
  const tenantId = getStoredTenantId();
  return tenantId ? { "X-Tenant-ID": tenantId } : {};
}

async function getJson<T = any>(path: string): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...getTenantHeaders()
  };

  const response = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `GET ${path} failed with ${response.status}`);
  }
  return response.json();
}

async function postJson<T = any>(path: string, payload: unknown): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...getTenantHeaders()
  };

  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `POST ${path} failed with ${response.status}`);
  }
  return response.json();
}

export { getStoredToken, saveToken, getStoredTenantId, saveTenantId, getJson, postJson };
