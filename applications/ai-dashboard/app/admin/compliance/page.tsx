"use client";

import { useEffect, useState, FormEvent } from "react";
import { getStoredToken, saveToken, getJson, postJson } from "../admin-api";
import RoleGuard from "../role-guard";
import TenantSelector from "../tenant-selector";

type ComplianceEvent = {
  id: string;
  event_type: string;
  status: string;
  details: Record<string, unknown>;
  created_at: string;
};

export default function ComplianceDashboardPage() {
  const [events, setEvents] = useState<ComplianceEvent[]>([]);
  const [eventType, setEventType] = useState("");
  const [status, setStatus] = useState("");
  const [details, setDetails] = useState("{}");
  const [token, setToken] = useState<string>(getStoredToken() || "");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    try {
      const response = await getJson<{ events: ComplianceEvent[] }>("/admin/compliance/events");
      setEvents(response.events || []);
      setMessage("");
    } catch (error) {
      setMessage(`Failed to load compliance events: ${String(error)}`);
    }
  }

  async function handleCreateEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const parsedDetails = JSON.parse(details || "{}");
      await postJson("/admin/compliance/event", {
        event_type: eventType,
        status,
        details: parsedDetails
      });
      setEventType("");
      setStatus("");
      setDetails("{}");
      setMessage("Compliance event recorded successfully.");
      await loadEvents();
    } catch (error) {
      setMessage(`Record compliance event failed: ${String(error)}`);
    }
  }

  function handleSaveToken() {
    saveToken(token);
    setMessage("Admin token saved locally.");
  }

  return (
    <main className="page-container">
      <section className="hero">
        <h1>Compliance Dashboard</h1>
        <p>Monitor compliance events and status for your AI Operations environment.</p>
        <p className="hint">Required permissions: <strong>compliance:read</strong> to view events, <strong>compliance:write</strong> to record compliance events.</p>
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

        <RoleGuard requiredPermissions={["compliance:write"]}>
          <form onSubmit={handleCreateEvent} className="form-card">
            <h2>Record Compliance Event</h2>
            <label>
              Event Type
              <input
                value={eventType}
                onChange={(event) => setEventType(event.target.value)}
                required
              />
            </label>
            <label>
              Status
              <input
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                required
              />
            </label>
            <label>
              Details (JSON)
              <textarea
                value={details}
                onChange={(event) => setDetails(event.target.value)}
                rows={6}
              />
            </label>
            <button type="submit">Record Event</button>
          </form>
        </RoleGuard>

        {message ? <p className="status-message">{message}</p> : null}

        <RoleGuard requiredPermissions={["compliance:read"]}>
          <div>
            <h2>Recent Compliance Events</h2>
            <button type="button" onClick={loadEvents}>Refresh Events</button>
            {events.length === 0 ? (
              <p>No compliance events available.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Details</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id}>
                      <td>{event.event_type}</td>
                      <td>{event.status}</td>
                      <td>{JSON.stringify(event.details)}</td>
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
