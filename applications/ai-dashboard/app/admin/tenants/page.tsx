"use client";

import { useEffect, useState, FormEvent } from "react";
import { getStoredToken, saveToken, getJson, postJson } from "../admin-api";
import RoleGuard from "../role-guard";
import TenantSelector from "../tenant-selector";

type Tenant = {
  id: string;
  name: string;
  organization_id: string;
  status: string;
  created_at: string | null;
  metadata: Record<string, unknown>;
};

export default function TenantManagementPage() {
  const [tenantName, setTenantName] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [token, setToken] = useState<string>(getStoredToken() || "");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    loadTenants();
  }, []);

  async function loadTenants() {
    try {
      const response = await getJson<{ tenants: Tenant[] }>("/admin/tenants");
      setTenants(response.tenants || []);
      setMessage("");
    } catch (error) {
      setMessage(`Failed to load tenants: ${String(error)}`);
    }
  }

  async function handleCreateTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const response = await postJson<{ tenant: Tenant }>("/admin/tenant", {
        tenant_name: tenantName,
        organization_id: organizationId
      });
      setTenants((current) => [response.tenant, ...current]);
      setTenantName("");
      setOrganizationId("");
      setMessage("Tenant created successfully.");
    } catch (error) {
      setMessage(`Create tenant failed: ${String(error)}`);
    }
  }

  function handleSaveToken() {
    saveToken(token);
    setMessage("Admin token saved locally.");
  }

  return (
    <main className="page-container">
      <section className="hero">
        <h1>Tenant Management</h1>
        <p>View and manage tenants in the AI Operations System.</p>
        <p className="hint">Required permissions: <strong>tenant:read</strong> to list tenants, <strong>tenant:write</strong> to create tenants.</p>
      </section>

      <section className="card">
        <div className="form-row">
          <label>Admin API Token</label>
          <input
            type="text"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Paste bearer token here"
          />
          <button type="button" onClick={handleSaveToken}>Save token</button>
        </div>

        <TenantSelector />

        <RoleGuard requiredPermissions={["tenant:write"]}>
          <form onSubmit={handleCreateTenant} className="form-card">
            <h2>Create Tenant</h2>
            <label>
              Tenant Name
              <input
                value={tenantName}
                onChange={(event) => setTenantName(event.target.value)}
                required
              />
            </label>
            <label>
              Organization ID
              <input
                value={organizationId}
                onChange={(event) => setOrganizationId(event.target.value)}
                required
              />
            </label>
            <button type="submit">Create Tenant</button>
          </form>
        </RoleGuard>

        <RoleGuard requiredPermissions={["tenant:read"]}>
          <div>
            <h2>Tenant List</h2>
            {tenants.length === 0 ? (
              <p>No tenants loaded yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Organization</th>
                    <th>Status</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {tenants.map((tenant) => (
                    <tr key={tenant.id}>
                      <td>{tenant.name}</td>
                      <td>{tenant.organization_id}</td>
                      <td>{tenant.status}</td>
                      <td>{tenant.created_at || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </RoleGuard>
      </section>
    </main>
  );
}
