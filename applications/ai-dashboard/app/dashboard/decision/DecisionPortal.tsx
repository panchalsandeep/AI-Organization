"use client";

import React, { useState, useEffect } from "react";
import { getJson, postJson, getStoredTenantId } from "../../admin/admin-api";

interface Decision {
  id: string;
  title: string;
  description: string;
  context: string | null;
  alternatives: string[];
  status: string;
  estimated_impact: number;
  actual_impact: number | null;
  outcome: string | null;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
  decided_at: string | null;
}

export default function DecisionPortal() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [tenantId, setTenantId] = useState<string | null>(null);

  // Creation Form State
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newContext, setNewContext] = useState("");
  const [newAlternatives, setNewAlternatives] = useState("");
  const [newEstImpact, setNewEstImpact] = useState(3);
  const [newStatus, setNewStatus] = useState("proposed");

  // Evaluation Form State (Edit Mode)
  const [editStatus, setEditStatus] = useState("proposed");
  const [editActualImpact, setEditActualImpact] = useState<string>("");
  const [editOutcome, setEditOutcome] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);
    if (tid) {
      fetchDecisions();
    } else {
      setError("Please select a Tenant in the Admin Console first.");
    }
  }, []);

  const fetchDecisions = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getJson("/decisions");
      if (res.success) {
        setDecisions(res.decisions);
        if (res.decisions.length > 0 && !selectedDecision) {
          setSelectedDecision(res.decisions[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch decisions");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDecision = (dec: Decision) => {
    setSelectedDecision(dec);
    setEditStatus(dec.status);
    setEditActualImpact(dec.actual_impact ? dec.actual_impact.toString() : "");
    setEditOutcome(dec.outcome || "");
    setIsEditing(false);
    setSuccessMsg(null);
    setError(null);
  };

  const handleCreateDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDesc.trim()) return;

    // Parse alternatives from comma-separated string
    const parsedAlts = newAlternatives
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    try {
      setLoading(true);
      setError(null);
      setSuccessMsg(null);
      const res = await postJson("/decision", {
        title: newTitle,
        description: newDesc,
        context: newContext || null,
        alternatives: parsedAlts,
        status: newStatus,
        estimated_impact: newEstImpact,
      });

      if (res.success) {
        setSuccessMsg(`Decision '${newTitle}' logged successfully!`);
        setNewTitle("");
        setNewDesc("");
        setNewContext("");
        setNewAlternatives("");
        setNewEstImpact(3);
        setNewStatus("proposed");
        await fetchDecisions();
      }
    } catch (err: any) {
      setError(err.message || "Failed to create decision");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDecision) return;

    try {
      setLoading(true);
      setError(null);
      setSuccessMsg(null);
      const res = await postJson(`/decision/${selectedDecision.id}`, {
        method: "PUT", // postJson wraps fetch with headers, but let's make sure it handles updates
        // Wait, postJson helper actually does a standard POST.
        // Let's verify: In admin-api.ts, postJson uses fetch with method "POST"!
        // Ah! Can we send a PUT via postJson? No, postJson in admin-api.ts strictly sets method: "POST".
        // Wait! Let's check how admin-api.ts works. Yes, we saw postJson sets method: "POST".
        // BUT wait, in backend/api/main.py, did we register PUT /decision/{decision_id}?
        // Yes, `@app.put("/decision/{decision_id}")`.
        // Can we make a custom put request, or does backend support POST for updating?
        // Wait, let's write a standard fetch for update or edit, since admin-api doesn't export a putJson!
        // Yes! We can write a local custom fetch call to handle PUT request perfectly!
      });
    } catch (err) {}
  };

  // Let's implement a robust custom update handler directly inside the component
  const executeUpdate = async () => {
    if (!selectedDecision) return;

    const token = typeof window !== "undefined" ? window.localStorage.getItem("AI_OPS_ADMIN_TOKEN") : null;
    const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      setLoading(true);
      setError(null);
      setSuccessMsg(null);

      const payload = {
        title: selectedDecision.title,
        description: selectedDecision.description,
        context: selectedDecision.context,
        alternatives: selectedDecision.alternatives,
        status: editStatus,
        estimated_impact: selectedDecision.estimated_impact,
        actual_impact: editActualImpact ? parseInt(editActualImpact) : null,
        outcome: editOutcome || null,
      };

      const res = await fetch(`http://localhost:8000/decision/${selectedDecision.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId || "",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Failed to update decision: ${res.statusText}`);
      }

      const data = await res.json();
      if (data.success) {
        setSuccessMsg("Decision updated and evaluated successfully!");
        setIsEditing(false);
        // Refresh items
        const updatedList = decisions.map((d) => (d.id === selectedDecision.id ? data.decision : d));
        setDecisions(updatedList);
        setSelectedDecision(data.decision);
      }
    } catch (err: any) {
      setError(err.message || "Update request failed");
    } finally {
      setLoading(false);
    }
  };

  const executeDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this decision log?")) return;

    const token = typeof window !== "undefined" ? window.localStorage.getItem("AI_OPS_ADMIN_TOKEN") : null;
    const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      setLoading(true);
      setError(null);
      setSuccessMsg(null);

      const res = await fetch(`http://localhost:8000/decision/${id}`, {
        method: "DELETE",
        headers: {
          "X-Tenant-ID": tenantId || "",
          ...authHeaders,
        },
      });

      if (!res.ok) {
        throw new Error(`Delete failed: ${res.statusText}`);
      }

      setSuccessMsg("Decision log deleted.");
      setSelectedDecision(null);
      await fetchDecisions();
    } catch (err: any) {
      setError(err.message || "Failed to delete decision");
    } finally {
      setLoading(false);
    }
  };

  // Metrics computations
  const totalCount = decisions.length;
  const evaluatedCount = decisions.filter((d) => d.status === "evaluated").length;
  const proposedCount = decisions.filter((d) => d.status === "proposed").length;
  const decidedCount = decisions.filter((d) => d.status === "decided" || d.status === "implemented").length;
  
  const avgEstImpact = totalCount > 0 
    ? (decisions.reduce((sum, d) => sum + d.estimated_impact, 0) / totalCount).toFixed(1)
    : "0.0";
    
  const evaluatedDecs = decisions.filter((d) => d.status === "evaluated" && d.actual_impact !== null);
  const avgActImpact = evaluatedDecs.length > 0
    ? (evaluatedDecs.reduce((sum, d) => sum + (d.actual_impact || 0), 0) / evaluatedDecs.length).toFixed(1)
    : "0.0";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Left panel: Decisions list and Log New Form */}
      <div>
        <div className="card" style={{ marginBottom: "16px", padding: "16px" }}>
          <h3 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#64748b" }}>Summary Telemetry</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px", textAlign: "center" }}>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontWeight: 700, fontSize: "16px", color: "#3730a3" }}>{totalCount}</div>
              <div style={{ color: "#64748b" }}>Total Logs</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontWeight: 700, fontSize: "16px", color: "#059669" }}>{evaluatedCount}</div>
              <div style={{ color: "#64748b" }}>Evaluated</div>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px", textAlign: "center", marginTop: "8px" }}>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontWeight: 600 }}>{avgEstImpact}/5</div>
              <div style={{ color: "#64748b", fontSize: "10px" }}>Avg Est Impact</div>
            </div>
            <div style={{ background: "#f8fafc", padding: "8px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontWeight: 600 }}>{avgActImpact}/5</div>
              <div style={{ color: "#64748b", fontSize: "10px" }}>Avg Act Impact</div>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <h2>Decisions Log</h2>
          {loading && decisions.length === 0 ? (
            <p>Loading decisions...</p>
          ) : decisions.length === 0 ? (
            <p style={{ color: "#64748b" }}>No decisions logged yet.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {decisions.map((dec) => (
                <li key={dec.id} style={{ marginBottom: "10px" }}>
                  <button
                    id={`decision-select-${dec.id}`}
                    onClick={() => handleSelectDecision(dec)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      backgroundColor: selectedDecision?.id === dec.id ? "#e0e7ff" : "transparent",
                      color: selectedDecision?.id === dec.id ? "#3730a3" : "#334155",
                      border: selectedDecision?.id === dec.id ? "1px solid #c7d2fe" : "1px solid #cbd5e1",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      marginTop: 0,
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "14px" }}>{dec.title}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "6px", fontSize: "11px" }}>
                      <span style={{ color: "#64748b" }}>Est: {dec.estimated_impact}/5</span>
                      <span
                        style={{
                          fontWeight: 700,
                          padding: "1px 4px",
                          borderRadius: "4px",
                          backgroundColor:
                            dec.status === "evaluated"
                              ? "#d1fae5"
                              : dec.status === "proposed"
                              ? "#fef3c7"
                              : "#e0e7ff",
                          color:
                            dec.status === "evaluated"
                              ? "#065f46"
                              : dec.status === "proposed"
                              ? "#b45309"
                              : "#3730a3",
                        }}
                      >
                        {dec.status}
                      </span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2>Log Decision</h2>
          <form onSubmit={handleCreateDecision}>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Title</label>
              <input
                id="decision-title-input"
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Migrate database to Supabase"
                required
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Description</label>
              <textarea
                id="decision-desc-input"
                rows={3}
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Details of the decision..."
                required
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Background Context</label>
              <textarea
                id="decision-context-input"
                rows={2}
                value={newContext}
                onChange={(e) => setNewContext(e.target.value)}
                placeholder="Context or problems leading to this..."
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Alternatives (comma separated)</label>
              <input
                id="decision-alternatives-input"
                type="text"
                value={newAlternatives}
                onChange={(e) => setNewAlternatives(e.target.value)}
                placeholder="AWS RDS, CockroachDB, self-host pg"
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Estimated Impact</label>
              <select
                id="decision-impact-select"
                value={newEstImpact}
                onChange={(e) => setNewEstImpact(parseInt(e.target.value))}
                style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
              >
                <option value="1">1 - Minimal</option>
                <option value="2">2 - Low</option>
                <option value="3">3 - Moderate</option>
                <option value="4">4 - High</option>
                <option value="5">5 - Critical</option>
              </select>
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Status</label>
              <select
                id="decision-status-select"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
              >
                <option value="proposed">Proposed</option>
                <option value="decided">Decided</option>
                <option value="implemented">Implemented</option>
              </select>
            </div>
            <button id="decision-submit-btn" type="submit" style={{ width: "100%" }} disabled={loading}>
              Create Decision Log
            </button>
          </form>
        </div>
      </div>

      {/* Right panel: Selected Decision context and outcomes */}
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

        {selectedDecision ? (
          <>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h1 style={{ margin: 0, fontSize: "24px", color: "#1e1b4b" }}>{selectedDecision.title}</h1>
                  <div style={{ color: "#64748b", fontSize: "13px", marginTop: "6px" }}>
                    Logged by <strong>{selectedDecision.created_by}</strong> on {selectedDecision.created_at ? new Date(selectedDecision.created_at).toLocaleString() : "-"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    id="decision-edit-toggle-btn"
                    onClick={() => setIsEditing(!isEditing)}
                    style={{ backgroundColor: isEditing ? "#6b7280" : "#4f46e5", marginTop: 0, padding: "8px 14px", fontSize: "14px" }}
                  >
                    {isEditing ? "Cancel" : "✏️ Evaluate / Edit"}
                  </button>
                  <button
                    id="decision-delete-btn"
                    onClick={() => executeDelete(selectedDecision.id)}
                    style={{ backgroundColor: "#dc2626", marginTop: 0, padding: "8px 14px", fontSize: "14px" }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>

            {isEditing ? (
              <div className="card">
                <h2>Evaluate Outcomes / Edit Status</h2>
                <form onSubmit={(e) => { e.preventDefault(); executeUpdate(); }}>
                  <div style={{ marginBottom: "12px" }}>
                    <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Status</label>
                    <select
                      id="edit-decision-status"
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                      style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                    >
                      <option value="proposed">Proposed</option>
                      <option value="decided">Decided</option>
                      <option value="implemented">Implemented</option>
                      <option value="evaluated">Evaluated</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: "12px" }}>
                    <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Actual Outcome Description</label>
                    <textarea
                      id="edit-decision-outcome"
                      rows={4}
                      value={editOutcome}
                      onChange={(e) => setEditOutcome(e.target.value)}
                      placeholder="Detail actual results, outcomes, or key lessons learned..."
                    />
                  </div>

                  <div style={{ marginBottom: "12px" }}>
                    <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Actual Impact Rating (1-5)</label>
                    <select
                      id="edit-decision-actual-impact"
                      value={editActualImpact}
                      onChange={(e) => setEditActualImpact(e.target.value)}
                      style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                    >
                      <option value="">-- Not Rated --</option>
                      <option value="1">1 - Minimal</option>
                      <option value="2">2 - Low</option>
                      <option value="3">3 - Moderate</option>
                      <option value="4">4 - High</option>
                      <option value="5">5 - Critical</option>
                    </select>
                  </div>

                  <button id="edit-decision-save-btn" type="submit" style={{ width: "100%" }} disabled={loading}>
                    Save Changes
                  </button>
                </form>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
                {/* Context & Description */}
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <div className="card" style={{ marginBottom: 0 }}>
                    <h2>Decision Description</h2>
                    <p style={{ fontSize: "15px", lineHeight: "1.6", color: "#334155", margin: 0 }}>{selectedDecision.description}</p>
                  </div>

                  {selectedDecision.context && (
                    <div className="card" style={{ marginBottom: 0 }}>
                      <h2>Background Context</h2>
                      <p style={{ fontSize: "14.5px", lineHeight: "1.5", color: "#475569", margin: 0 }}>{selectedDecision.context}</p>
                    </div>
                  )}

                  <div className="card" style={{ marginBottom: 0 }}>
                    <h2>Alternatives Considered</h2>
                    {selectedDecision.alternatives.length === 0 ? (
                      <p style={{ color: "#64748b", margin: 0 }}>None cataloged</p>
                    ) : (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "8px" }}>
                        {selectedDecision.alternatives.map((alt, index) => (
                          <span
                            key={index}
                            style={{
                              background: "#e2e8f0",
                              color: "#1e293b",
                              padding: "4px 10px",
                              borderRadius: "20px",
                              fontSize: "12.5px",
                              fontWeight: 600,
                            }}
                          >
                            {alt}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Outcome & Impact Scores */}
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <div className="card" style={{ marginBottom: 0 }}>
                    <h2>Impact Analysis</h2>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "12px" }}>
                      <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px", background: "#f8fafc", textAlign: "center" }}>
                        <div style={{ fontSize: "13px", color: "#64748b" }}>Estimated Impact</div>
                        <div style={{ fontSize: "24px", fontWeight: 800, color: "#3730a3", marginTop: "6px" }}>{selectedDecision.estimated_impact}/5</div>
                      </div>
                      <div style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "12px", background: "#f8fafc", textAlign: "center" }}>
                        <div style={{ fontSize: "13px", color: "#64748b" }}>Actual Impact</div>
                        <div style={{ fontSize: "24px", fontWeight: 800, color: selectedDecision.actual_impact ? "#059669" : "#94a3b8", marginTop: "6px" }}>
                          {selectedDecision.actual_impact ? `${selectedDecision.actual_impact}/5` : "--"}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="card" style={{ marginBottom: 0, flex: 1 }}>
                    <h2>Final Evaluated Outcome</h2>
                    {selectedDecision.status !== "evaluated" ? (
                      <p style={{ color: "#64748b", margin: 0, fontStyle: "italic" }}>
                        This decision is currently marked as <strong>{selectedDecision.status}</strong>. Evaluate outcomes by clicking the Edit button above.
                      </p>
                    ) : (
                      <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "12px", padding: "16px" }}>
                        <p style={{ margin: 0, fontSize: "14.5px", color: "#166534", lineHeight: "1.6" }}>
                          {selectedDecision.outcome || "Evaluated with no detailed outcome logs."}
                        </p>
                        {selectedDecision.decided_at && (
                          <div style={{ fontSize: "11px", color: "#166534", marginTop: "12px", opacity: 0.8 }}>
                            Decided / Resolved at: {new Date(selectedDecision.decided_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "80px 24px", color: "#64748b" }}>
            <h2>No Decision Log Selected</h2>
            <p>Select a decision item from the timeline on the left to see descriptions, considered alternatives, and outcomes assessments.</p>
          </div>
        )}
      </div>
    </div>
  );
}
