"use client";

import React, { useState, useEffect } from "react";
import { getJson, postJson, getStoredTenantId } from "../../admin/admin-api";

interface Integration {
  id: string;
  name: string;
  integration_type: string;
  status: string;
  last_sync: string | null;
}

interface SyncLog {
  id: string;
  records_synced: number;
  status: string;
  error_message: string | null;
  timestamp: string | null;
}

export default function IntegrationsPanel() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [syncLogs, setSyncLogs] = useState<SyncLog[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);

  // Form inputs
  const [name, setName] = useState("");
  const [integrationType, setIntegrationType] = useState("slack");
  const [configField1, setConfigField1] = useState("");
  const [configField2, setConfigField2] = useState("");

  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);
    if (tid) {
      fetchIntegrations();
    } else {
      setError("Please configure an active Tenant in the Admin Console first.");
    }
  }, []);

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getJson("/integrations");
      if (res.success) {
        setIntegrations(res.integrations);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load integrations");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectIntegration = async (integration: Integration) => {
    setSelectedIntegration(integration);
    fetchSyncLogs(integration.id);
  };

  const fetchSyncLogs = async (id: string) => {
    try {
      const res = await getJson(`/integration/${id}/sync-logs?limit=10`);
      if (res.success) {
        setSyncLogs(res.logs);
      }
    } catch (err: any) {
      console.error("Failed to fetch sync logs:", err);
    }
  };

  const handleCreateIntegration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    // Build configuration payload according to selected integration type
    let configPayload: Record<string, any> = {};
    if (integrationType === "slack") {
      configPayload = { bot_token: configField1 || "mock-token" };
    } else if (integrationType === "notion") {
      configPayload = { api_key: configField1 || "mock-key" };
    } else if (integrationType === "google_drive") {
      configPayload = { api_key: configField1 || "mock-drive-key", credentials_json: configField2 || null };
    } else if (integrationType === "github") {
      configPayload = { personal_access_token: configField1 || "mock-pat", username: configField2 || "mock-user" };
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMsg(null);
      const res = await postJson("/integration", {
        name,
        integration_type: integrationType,
        config: configPayload,
      });

      if (res.success) {
        setSuccessMsg(`Integration '${name}' added successfully!`);
        setName("");
        setConfigField1("");
        setConfigField2("");
        fetchIntegrations();
      }
    } catch (err: any) {
      setError(err.message || "Failed to create integration");
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (integration: Integration) => {
    setActionLoading(`test-${integration.id}`);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await postJson(`/integration/${integration.id}/test`, {});
      if (res.success) {
        setSuccessMsg(res.connected ? `Successfully connected to ${integration.name}!` : `Connection failed for ${integration.name}.`);
        fetchIntegrations();
        if (selectedIntegration?.id === integration.id) {
          handleSelectIntegration({ ...integration, status: res.connected ? "connected" : "error" });
        }
      }
    } catch (err: any) {
      setError(err.message || "Test connection request failed");
    } finally {
      setActionLoading(null);
    }
  };

  const handleTriggerSync = async (integration: Integration) => {
    setActionLoading(`sync-${integration.id}`);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await postJson(`/integration/${integration.id}/sync`, {});
      if (res.success) {
        setSuccessMsg(`Sync complete! Synced ${res.sync?.records_synced ?? 0} records.`);
        fetchIntegrations();
        fetchSyncLogs(integration.id);
      }
    } catch (err: any) {
      setError(err.message || "Sync execution failed");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Left Column: Integration list & configuration creation */}
      <div>
        <div className="card">
          <h2>Active Connectors</h2>
          {loading && integrations.length === 0 ? (
            <p>Loading connectors...</p>
          ) : integrations.length === 0 ? (
            <p style={{ color: "#64748b" }}>No integration connectors configured.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {integrations.map((integration) => (
                <li key={integration.id} style={{ marginBottom: "12px" }}>
                  <button
                    id={`integration-item-${integration.id}`}
                    onClick={() => handleSelectIntegration(integration)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      backgroundColor: selectedIntegration?.id === integration.id ? "#e0e7ff" : "transparent",
                      color: selectedIntegration?.id === integration.id ? "#3730a3" : "#334155",
                      border: selectedIntegration?.id === integration.id ? "1px solid #c7d2fe" : "1px solid #cbd5e1",
                      padding: "10px 14px",
                      borderRadius: "10px",
                      cursor: "pointer",
                      marginTop: 0,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong style={{ fontSize: "15px" }}>{integration.name}</strong>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor:
                            integration.status === "connected"
                              ? "#d1fae5"
                              : integration.status === "error"
                              ? "#fee2e2"
                              : "#f3f4f6",
                          color:
                            integration.status === "connected"
                              ? "#065f46"
                              : integration.status === "error"
                              ? "#991b1b"
                              : "#374151",
                        }}
                      >
                        {integration.status}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>
                      Type: {integration.integration_type}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2>New Integration</h2>
          <form onSubmit={handleCreateIntegration}>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Connector Name</label>
              <input
                id="integration-name-input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Corp Notion Vault"
                required
              />
            </div>

            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Integration Type</label>
              <select
                id="integration-type-select"
                value={integrationType}
                onChange={(e) => {
                  setIntegrationType(e.target.value);
                  setConfigField1("");
                  setConfigField2("");
                }}
                style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
              >
                <option value="slack">Slack</option>
                <option value="notion">Notion Workspace</option>
                <option value="google_drive">Google Drive</option>
                <option value="github">GitHub Organization</option>
              </select>
            </div>

            {/* Dynamic configuration inputs based on type */}
            {integrationType === "slack" && (
              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Bot User OAuth Token</label>
                <input
                  id="config-slack-token"
                  type="password"
                  value={configField1}
                  onChange={(e) => setConfigField1(e.target.value)}
                  placeholder="xoxb-..."
                />
              </div>
            )}

            {integrationType === "notion" && (
              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Internal Integration Token</label>
                <input
                  id="config-notion-key"
                  type="password"
                  value={configField1}
                  onChange={(e) => setConfigField1(e.target.value)}
                  placeholder="secret_..."
                />
              </div>
            )}

            {integrationType === "google_drive" && (
              <>
                <div style={{ marginBottom: "12px" }}>
                  <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>API Key</label>
                  <input
                    id="config-gdrive-key"
                    type="password"
                    value={configField1}
                    onChange={(e) => setConfigField1(e.target.value)}
                    placeholder="Enter API key"
                  />
                </div>
                <div style={{ marginBottom: "12px" }}>
                  <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Credentials JSON (optional)</label>
                  <input
                    id="config-gdrive-json"
                    type="text"
                    value={configField2}
                    onChange={(e) => setConfigField2(e.target.value)}
                    placeholder='{"type": "service_account", ...}'
                  />
                </div>
              </>
            )}

            {integrationType === "github" && (
              <>
                <div style={{ marginBottom: "12px" }}>
                  <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Personal Access Token</label>
                  <input
                    id="config-github-pat"
                    type="password"
                    value={configField1}
                    onChange={(e) => setConfigField1(e.target.value)}
                    placeholder="ghp_..."
                  />
                </div>
                <div style={{ marginBottom: "12px" }}>
                  <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>GitHub Username / Owner</label>
                  <input
                    id="config-github-owner"
                    type="text"
                    value={configField2}
                    onChange={(e) => setConfigField2(e.target.value)}
                    placeholder="e.g. octocat"
                  />
                </div>
              </>
            )}

            <button id="integration-submit-btn" type="submit" style={{ width: "100%" }} disabled={loading}>
              Create Integration
            </button>
          </form>
        </div>
      </div>

      {/* Right Column: Connection Details, Test Connection, Sync Action, Sync Logs History */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {error && (
          <div className="card error-card" style={{ padding: "16px", background: "#fef2f2", borderColor: "#fecaca" }}>
            <p style={{ margin: 0, color: "#991b1b" }}>{error}</p>
          </div>
        )}

        {successMsg && (
          <div className="card" style={{ padding: "16px", background: "#f0fdf4", borderColor: "#bbf7d0" }}>
            <p style={{ margin: 0, color: "#166534", fontWeight: 600 }}>{successMsg}</p>
          </div>
        )}

        {selectedIntegration ? (
          <>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h1 style={{ margin: 0, fontSize: "24px" }}>{selectedIntegration.name}</h1>
                  <p style={{ margin: "4px 0 0 0", color: "#64748b" }}>
                    Status: <strong style={{ textTransform: "capitalize" }}>{selectedIntegration.status}</strong>
                    {selectedIntegration.last_sync && (
                      <> | Last Synced: <strong>{new Date(selectedIntegration.last_sync).toLocaleString()}</strong></>
                    )}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "12px" }}>
                  <button
                    id={`test-conn-btn-${selectedIntegration.id}`}
                    onClick={() => handleTestConnection(selectedIntegration)}
                    disabled={actionLoading !== null}
                    style={{ backgroundColor: "#4b5563", marginTop: 0 }}
                  >
                    {actionLoading === `test-${selectedIntegration.id}` ? "Testing..." : "🔌 Test Connection"}
                  </button>
                  <button
                    id={`sync-now-btn-${selectedIntegration.id}`}
                    onClick={() => handleTriggerSync(selectedIntegration)}
                    disabled={actionLoading !== null}
                    style={{ backgroundColor: "#4f46e5", marginTop: 0 }}
                  >
                    {actionLoading === `sync-${selectedIntegration.id}` ? "Syncing..." : "🔄 Trigger Sync"}
                  </button>
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Synchronization History</h2>
              {syncLogs.length === 0 ? (
                <p style={{ color: "#64748b" }}>No synchronization attempts logged for this connector.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Records Synced</th>
                      <th>Status</th>
                      <th>Details / Error Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {syncLogs.map((log) => (
                      <tr key={log.id}>
                        <td>{log.timestamp ? new Date(log.timestamp).toLocaleString() : "-"}</td>
                        <td style={{ fontWeight: 600 }}>{log.records_synced}</td>
                        <td>
                          <span
                            style={{
                              fontSize: "11px",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              backgroundColor: log.status === "success" ? "#d1fae5" : "#fee2e2",
                              color: log.status === "success" ? "#065f46" : "#991b1b",
                            }}
                          >
                            {log.status}
                          </span>
                        </td>
                        <td style={{ color: log.status === "failed" ? "#dc2626" : "#475569" }}>
                          {log.error_message || "Completed successfully"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "80px 24px", color: "#64748b" }}>
            <h2>No Connector Selected</h2>
            <p>Select an integration connector from the list on the left to see sync logs, run a connection check, or manual sync remote data.</p>
          </div>
        )}
      </div>
    </div>
  );
}
