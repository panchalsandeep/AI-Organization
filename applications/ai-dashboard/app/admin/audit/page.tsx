"use client";

import { useEffect, useState, FormEvent } from "react";
import { getStoredToken, saveToken, getJson } from "../admin-api";
import RoleGuard from "../role-guard";
import TenantSelector from "../tenant-selector";

type AuditEvent = {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  changes: Record<string, unknown>;
  ip_address: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export default function AuditTrailPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [token, setToken] = useState<string>(getStoredToken() || "");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    try {
      const response = await getJson<{ events: AuditEvent[] }>("/admin/audit/events");
      setEvents(response.events || []);
      setMessage("");
    } catch (error) {
      setMessage(`Failed to load audit events: ${String(error)}`);
    }
  }

  function handleSaveToken() {
    saveToken(token);
    setMessage("Admin token saved locally.");
  }

  return (
    <main className="page-container">
      <section className="hero">
        <h1>Audit Trail</h1>
        <p>Track system activity and audit events across your enterprise.</p>
        <p className="hint">Required permission: <strong>audit:read</strong> to view audit events.</p>
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

        <RoleGuard requiredPermissions={["audit:read"]}>
          <div className="card">
            <h2>Recent Audit Events</h2>
            {message ? <p className="status-message">{message}</p> : null}
            <button type="button" onClick={loadEvents}>Refresh Events</button>
            {events.length === 0 ? (
              <p>No audit events available.</p>
            ) : (
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Details</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td>{event.user_id}</td>
                    <td>{event.action}</td>
                    <td>{event.resource_type} / {event.resource_id}</td>
                    <td>{JSON.stringify(event.changes)}</td>
                    <td>{event.created_at}</td>
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
