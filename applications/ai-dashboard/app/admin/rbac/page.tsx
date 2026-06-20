"use client";

import { useEffect, useState, FormEvent } from "react";
import { getStoredToken, saveToken, getJson, postJson } from "../admin-api";
import RoleGuard from "../role-guard";
import TenantSelector from "../tenant-selector";

type Role = {
  id: string;
  name: string;
  permissions: string[];
  created_at: string | null;
};

export default function RBACManagementPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [roleName, setRoleName] = useState("");
  const [permissions, setPermissions] = useState("");
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRoleId, setAssignRoleId] = useState("");
  const [permissionsUserId, setPermissionsUserId] = useState("");
  const [userPermissions, setUserPermissions] = useState<string[]>([]);
  const [token, setToken] = useState<string>(getStoredToken() || "");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    loadRoles();
  }, []);

  async function loadRoles() {
    try {
      const response = await getJson<{ roles: Role[] }>("/admin/roles");
      setRoles(response.roles || []);
      setMessage("");
    } catch (error) {
      setMessage(`Failed to load roles: ${String(error)}`);
    }
  }

  async function handleCreateRole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const rolePermissions = permissions.split(",").map((item) => item.trim()).filter(Boolean);
      const response = await postJson<{ role: Role }>("/admin/role", {
        role_name: roleName,
        permissions: rolePermissions
      });
      setRoles((current) => [response.role, ...current]);
      setRoleName("");
      setPermissions("");
      setMessage("Role created successfully.");
    } catch (error) {
      setMessage(`Create role failed: ${String(error)}`);
    }
  }

  async function handleAssignRole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await postJson("/admin/assign-role", {
        user_id: assignUserId,
        role_id: assignRoleId
      });
      setAssignUserId("");
      setAssignRoleId("");
      setMessage("Role assigned successfully.");
    } catch (error) {
      setMessage(`Assign role failed: ${String(error)}`);
    }
  }

  async function handleLoadPermissions(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const response = await getJson<{ permissions: string[] }>(`/admin/user/${encodeURIComponent(permissionsUserId)}/permissions`);
      setUserPermissions(response.permissions || []);
      setMessage("");
    } catch (error) {
      setMessage(`Load permissions failed: ${String(error)}`);
    }
  }

  function handleSaveToken() {
    saveToken(token);
    setMessage("Admin token saved locally.");
  }

  return (
    <main className="page-container">
      <section className="hero">
        <h1>RBAC Management</h1>
        <p>Review and configure roles and permissions for your organization.</p>
        <p className="hint">Required permissions: <strong>role:read</strong> to view roles and user permissions, <strong>role:write</strong> to create or assign roles.</p>
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

        {message ? <p className="status-message">{message}</p> : null}

        <RoleGuard requiredPermissions={["role:write"]}>
          <div>
            <form onSubmit={handleCreateRole} className="form-card">
              <h2>Create Role</h2>
              <label>
                Role Name
                <input
                  value={roleName}
                  onChange={(event) => setRoleName(event.target.value)}
                  required
                />
              </label>
              <label>
                Permissions (comma-separated)
                <input
                  value={permissions}
                  onChange={(event) => setPermissions(event.target.value)}
                  placeholder="tenant:read, role:write, audit:read"
                />
              </label>
              <button type="submit">Create Role</button>
            </form>

            <form onSubmit={handleAssignRole} className="form-card">
              <h2>Assign Role</h2>
              <label>
                User ID
                <input
                  value={assignUserId}
                  onChange={(event) => setAssignUserId(event.target.value)}
                  required
                />
              </label>
              <label>
                Role ID
                <input
                  value={assignRoleId}
                  onChange={(event) => setAssignRoleId(event.target.value)}
                  required
                />
              </label>
              <button type="submit">Assign Role</button>
            </form>
          </div>
        </RoleGuard>

        <RoleGuard requiredPermissions={["role:read"]}>
          <div>
            <form onSubmit={handleLoadPermissions} className="form-card">
              <h2>Fetch User Permissions</h2>
              <label>
                User ID
                <input
                  value={permissionsUserId}
                  onChange={(event) => setPermissionsUserId(event.target.value)}
                  required
                />
              </label>
              <button type="submit">Load Permissions</button>
            </form>

            {userPermissions.length > 0 ? (
              <div className="card">
                <h3>User Permissions</h3>
                <ul>
                  {userPermissions.map((permission) => (
                    <li key={permission}>{permission}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div>
              <h2>Roles</h2>
              {roles.length === 0 ? (
                <p>No roles loaded yet.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Permissions</th>
                      <th>Created At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {roles.map((role) => (
                      <tr key={role.id}>
                        <td>{role.name}</td>
                        <td>{role.permissions.join(", ")}</td>
                        <td>{role.created_at || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </RoleGuard>
      </section>
    </main>
  );
}
