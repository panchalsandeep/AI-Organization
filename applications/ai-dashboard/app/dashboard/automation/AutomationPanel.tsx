"use client";

import React, { useState, useEffect } from "react";
import { getJson, postJson, getStoredTenantId } from "../../admin/admin-api";

interface Workflow {
  id: string;
  name: string;
  active: boolean;
}

interface ExecutionLog {
  execution_id: string;
  workflow_id: string;
  status: string;
  started_at: string;
  finished_at: string;
  duration_seconds: number;
  error?: string;
}

export default function AutomationPanel() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [executionLogs, setExecutionLogs] = useState<ExecutionLog[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);

  // Trigger form states
  const [payloadText, setPayloadText] = useState("{\n  \"source\": \"dashboard\",\n  \"event\": \"manual_trigger\"\n}");
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<any | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);
    if (tid) {
      fetchWorkflows();
    } else {
      setError("Please select a Tenant in the Admin Console first.");
    }
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getJson("/automation/n8n/workflows");
      if (res.success) {
        setWorkflows(res.workflows);
        if (res.workflows.length > 0 && !selectedWorkflow) {
          handleSelectWorkflow(res.workflows[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load n8n workflows");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectWorkflow = async (wf: Workflow) => {
    setSelectedWorkflow(wf);
    fetchExecutionLogs(wf.id);
    setTriggerResult(null);
    setSuccessMsg(null);
  };

  const fetchExecutionLogs = async (id: string) => {
    try {
      setError(null);
      const res = await getJson(`/automation/n8n/${id}/logs`);
      if (res.success) {
        setExecutionLogs(res.logs);
      }
    } catch (err: any) {
      console.error("Failed to load execution logs:", err);
    }
  };

  const handleTriggerWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkflow) return;

    let parsedPayload = {};
    try {
      parsedPayload = JSON.parse(payloadText);
    } catch (err) {
      setError("Invalid payload JSON formatting.");
      return;
    }

    try {
      setTriggering(true);
      setError(null);
      setSuccessMsg(null);
      const res = await postJson("/automation/n8n/trigger", {
        workflow_id: selectedWorkflow.id,
        payload: parsedPayload,
      });

      if (res.success) {
        setSuccessMsg(`Workflow '${selectedWorkflow.name}' triggered successfully!`);
        setTriggerResult(res.result);
        // Refresh logs after brief interval
        setTimeout(() => {
          fetchExecutionLogs(selectedWorkflow.id);
        }, 1000);
      }
    } catch (err: any) {
      setError(err.message || "Failed to trigger workflow");
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Left panel: list of n8n workflows */}
      <div>
        <div className="card">
          <h2>n8n Workflows</h2>
          {loading && workflows.length === 0 ? (
            <p>Loading workflows...</p>
          ) : workflows.length === 0 ? (
            <p style={{ color: "#64748b" }}>No workflows found inside n8n.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {workflows.map((wf) => (
                <li key={wf.id} style={{ marginBottom: "10px" }}>
                  <button
                    id={`workflow-item-${wf.id}`}
                    onClick={() => handleSelectWorkflow(wf)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      backgroundColor: selectedWorkflow?.id === wf.id ? "#e0e7ff" : "transparent",
                      color: selectedWorkflow?.id === wf.id ? "#3730a3" : "#334155",
                      border: selectedWorkflow?.id === wf.id ? "1px solid #c7d2fe" : "1px solid #cbd5e1",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      marginTop: 0,
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{wf.name}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "6px" }}>
                      <span style={{ fontSize: "11px", color: "#64748b" }}>ID: {wf.id}</span>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "1px 5px",
                          borderRadius: "4px",
                          backgroundColor: wf.active ? "#d1fae5" : "#f3f4f6",
                          color: wf.active ? "#065f46" : "#4b5563",
                        }}
                      >
                        {wf.active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Right panel: executions and triggers */}
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

        {selectedWorkflow ? (
          <>
            {/* Header info */}
            <div className="card">
              <h1 style={{ margin: 0, fontSize: "22px", color: "#1e1b4b" }}>{selectedWorkflow.name}</h1>
              <p style={{ margin: "4px 0 0 0", color: "#64748b", fontSize: "14px" }}>
                Workflow Identifier: <strong>{selectedWorkflow.id}</strong> | Status:{" "}
                <strong>{selectedWorkflow.active ? "Active & Listening" : "Inactive"}</strong>
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
              {/* Trigger panel */}
              <div className="card">
                <h2>Trigger Webhook</h2>
                <form onSubmit={handleTriggerWorkflow}>
                  <label style={{ display: "block", marginBottom: "6px" }}>Input Variables Payload (JSON)</label>
                  <textarea
                    id="workflow-payload-input"
                    rows={6}
                    value={payloadText}
                    onChange={(e) => setPayloadText(e.target.value)}
                    style={{ fontFamily: "monospace", fontSize: "13px" }}
                    required
                  />
                  <button
                    id="workflow-trigger-btn"
                    type="submit"
                    disabled={triggering}
                    style={{ width: "100%", backgroundColor: "#4f46e5" }}
                  >
                    {triggering ? "Firing Webhook..." : "⚡ Execute Workflow Run"}
                  </button>
                </form>

                {triggerResult && (
                  <div style={{ marginTop: "18px", padding: "12px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "10px" }}>
                    <h3 style={{ margin: "0 0 6px 0", fontSize: "14px" }}>Trigger Response</h3>
                    <pre style={{ fontSize: "11px", color: "#334155" }}>
                      {JSON.stringify(triggerResult, null, 2)}
                    </pre>
                  </div>
                )}
              </div>

              {/* Executions log */}
              <div className="card">
                <h2>Execution History Logs</h2>
                {executionLogs.length === 0 ? (
                  <p style={{ color: "#64748b" }}>No execution runs logged for this workflow.</p>
                ) : (
                  <div style={{ maxHeight: "400px", overflowY: "auto" }}>
                    {executionLogs.map((log) => (
                      <div
                        key={log.execution_id}
                        style={{
                          padding: "12px",
                          border: "1px solid #e2e8f0",
                          borderRadius: "10px",
                          background: log.status === "success" ? "#f0fdf4" : "#fef2f2",
                          marginBottom: "12px",
                          fontSize: "13px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
                          <span>Run ID: {log.execution_id}</span>
                          <span
                            style={{
                              color: log.status === "success" ? "#166534" : "#991b1b",
                              textTransform: "uppercase",
                              fontSize: "11px",
                            }}
                          >
                            {log.status === "success" ? "✅ Success" : "❌ Failed"}
                          </span>
                        </div>
                        <div style={{ marginTop: "6px", color: "#64748b" }}>
                          Started: {new Date(log.started_at).toLocaleString()}
                        </div>
                        <div style={{ color: "#64748b" }}>
                          Duration: {log.duration_seconds}s
                        </div>
                        {log.error && (
                          <div style={{ marginTop: "6px", color: "#b91c1c", fontWeight: 600 }}>
                            Error: {log.error}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "80px 24px", color: "#64748b" }}>
            <h2>No Workflow Selected</h2>
            <p>Select a workflow from the list on the left to start debugging execution logs and run manual webhook tests.</p>
          </div>
        )}
      </div>
    </div>
  );
}
