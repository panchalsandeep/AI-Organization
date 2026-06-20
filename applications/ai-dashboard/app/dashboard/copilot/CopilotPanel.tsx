"use client";

import React, { useState, useEffect, useRef } from "react";
import { postJson, getStoredTenantId } from "../../admin/admin-api";

interface Message {
  sender: "user" | "copilot";
  text: string;
  suggestedAction?: {
    action: string;
    integration_id?: string;
    [key: string]: any;
  } | null;
}

interface TenantContext {
  tenant_id: string;
  kpi_count: number;
  kpis_list: string[];
  active_integrations: string[];
  recent_meetings: string[];
}

export default function CopilotPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "copilot",
      text: "Hello! I am your AI Operations Copilot. Ask me questions about your active integrations, KPIs, meetings, or tell me to run synchronization actions.",
    },
  ]);
  const [input, setInput] = useState("");
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [currentContext, setCurrentContext] = useState<TenantContext | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setTenantId(getStoredTenantId());
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessageText = input;
    setMessages((prev) => [...prev, { sender: "user", text: userMessageText }]);
    setInput("");
    setLoading(true);
    setError(null);
    setActionSuccess(null);

    try {
      const res = await postJson("/copilot/ask", { query: userMessageText });
      if (res.success && res.result) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "copilot",
            text: res.result.response,
            suggestedAction: res.result.suggested_action,
          },
        ]);
        if (res.result.context) {
          setCurrentContext(res.result.context);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to communicate with Copilot");
      setMessages((prev) => [
        ...prev,
        {
          sender: "copilot",
          text: "I encountered an error trying to process that instruction. Please check your backend connection.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAction = async (action: any) => {
    setError(null);
    setActionSuccess(null);
    try {
      if (action.action === "sync" && action.integration_id) {
        setMessages((prev) => [
          ...prev,
          { sender: "copilot", text: `🔄 Starting recommended integration sync for ID: ${action.integration_id}...` },
        ]);
        const res = await postJson(`/integration/${action.integration_id}/sync`, {});
        if (res.success) {
          setActionSuccess("Sync action executed successfully!");
          setMessages((prev) => [
            ...prev,
            { sender: "copilot", text: `✅ Sync completed! Successfully loaded ${res.sync?.records_synced ?? 0} data records.` },
          ]);
        }
      } else {
        // Fallback for other generic automation commands
        setMessages((prev) => [
          ...prev,
          { sender: "copilot", text: `⚙️ Firing generic action trigger...` },
        ]);
        const res = await postJson("/automation/n8n/trigger", {
          workflow_id: action.workflow_id || "wf-sync-1",
          payload: action.payload || {},
        });
        if (res.success) {
          setActionSuccess("Automation workflow triggered successfully!");
          setMessages((prev) => [
            ...prev,
            { sender: "copilot", text: `✅ Webhook run created with ID: ${res.result?.execution_id}` },
          ]);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to execute recommended action.");
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "24px", minHeight: "600px" }}>
      {/* Left panel: Chat Interface */}
      <div className="card" style={{ display: "flex", flexDirection: "column", height: "600px", padding: "20px" }}>
        <div style={{ borderBottom: "1px solid #e2e8f0", paddingBottom: "12px", marginBottom: "16px" }}>
          <h2 style={{ margin: 0 }}>AI Operations Assistant</h2>
          <p style={{ margin: "4px 0 0 0", fontSize: "14px", color: "#64748b" }}>
            Active Context: <strong>{tenantId || "None selected"}</strong>
          </p>
        </div>

        {/* Chat Feed */}
        <div
          style={{
            flex: 1,
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            padding: "16px",
            overflowY: "auto",
            marginBottom: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          {messages.map((msg, index) => {
            const isCopilot = msg.sender === "copilot";
            return (
              <div
                key={index}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: isCopilot ? "flex-start" : "flex-end",
                }}
              >
                <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "2px" }}>
                  {isCopilot ? "🤖 AI Copilot" : "You"}
                </div>
                <div
                  style={{
                    background: isCopilot ? "#ffffff" : "#4f46e5",
                    color: isCopilot ? "#0f172a" : "#ffffff",
                    border: isCopilot ? "1px solid #e2e8f0" : "none",
                    padding: "10px 16px",
                    borderRadius: isCopilot ? "12px 12px 12px 0" : "12px 12px 0 12px",
                    maxWidth: "85%",
                    fontSize: "14.5px",
                    lineHeight: "1.45",
                    boxShadow: isCopilot ? "0 4px 6px -1px rgba(0,0,0,0.05)" : "none",
                  }}
                >
                  <div>{msg.text}</div>
                  
                  {/* Action recommendation link */}
                  {isCopilot && msg.suggestedAction && (
                    <div style={{ marginTop: "12px", borderTop: "1px solid #e2e8f0", paddingTop: "8px" }}>
                      <p style={{ margin: "0 0 8px 0", fontSize: "12px", fontWeight: 600, color: "#4f46e5" }}>
                        💡 Recommended Workspace Action Detected:
                      </p>
                      <button
                        id={`copilot-action-btn-${index}`}
                        onClick={() => handleExecuteAction(msg.suggestedAction)}
                        style={{
                          marginTop: 0,
                          padding: "6px 12px",
                          fontSize: "12.5px",
                          backgroundColor: "#312e81",
                        }}
                      >
                        ⚡ Execute Action
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
              <span style={{ fontSize: "12px", color: "#64748b" }}>🤖 AI Copilot</span>
              <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", padding: "10px 16px", borderRadius: "12px 12px 12px 0", color: "#94a3b8", fontSize: "14px" }}>
                Thinking...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Errors & Status logs */}
        {error && (
          <div style={{ color: "#b91c1c", fontSize: "13px", marginBottom: "8px", fontWeight: 600 }}>
            ⚠️ {error}
          </div>
        )}
        {actionSuccess && (
          <div style={{ color: "#15803d", fontSize: "13px", marginBottom: "8px", fontWeight: 600 }}>
            🎉 {actionSuccess}
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSendMessage} style={{ display: "flex", gap: "8px" }}>
          <input
            id="copilot-input-field"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask copilot to compile KPIs, review meetings, or run data syncs..."
            style={{ flex: 1 }}
            required
            disabled={loading}
          />
          <button id="copilot-send-btn" type="submit" disabled={loading || !input.trim()}>
            Ask
          </button>
        </form>
      </div>

      {/* Right panel: Live tenant context status retrieved by Copilot */}
      <div>
        <div className="card" style={{ height: "600px", overflowY: "auto" }}>
          <h2>Workspace Context</h2>
          {currentContext ? (
            <div style={{ fontSize: "13.5px", display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <strong style={{ color: "#475569" }}>Tenant Identifier:</strong>
                <div style={{ wordBreak: "break-all", background: "#f8fafc", padding: "6px 10px", borderRadius: "6px", border: "1px solid #e2e8f0", marginTop: "4px", fontWeight: 600 }}>
                  {currentContext.tenant_id}
                </div>
              </div>

              <div>
                <strong style={{ color: "#475569" }}>Configured KPIs:</strong>
                <span style={{ marginLeft: "6px", background: "#e0e7ff", color: "#3730a3", padding: "2px 6px", borderRadius: "4px", fontSize: "11px", fontWeight: 700 }}>
                  {currentContext.kpi_count}
                </span>
                {currentContext.kpis_list.length === 0 ? (
                  <div style={{ color: "#94a3b8", marginTop: "4px", fontStyle: "italic" }}>None configured</div>
                ) : (
                  <ul style={{ paddingLeft: "16px", margin: "6px 0 0 0" }}>
                    {currentContext.kpis_list.map((name, i) => (
                      <li key={i}>{name}</li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <strong style={{ color: "#475569" }}>Active Sync Integrations:</strong>
                {currentContext.active_integrations.length === 0 ? (
                  <div style={{ color: "#94a3b8", marginTop: "4px", fontStyle: "italic" }}>None online</div>
                ) : (
                  <ul style={{ paddingLeft: "16px", margin: "6px 0 0 0" }}>
                    {currentContext.active_integrations.map((name, i) => (
                      <li key={i} style={{ color: "#166534", fontWeight: 600 }}>🟢 {name}</li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <strong style={{ color: "#475569" }}>Recent Meetings Summarized:</strong>
                {currentContext.recent_meetings.length === 0 ? (
                  <div style={{ color: "#94a3b8", marginTop: "4px", fontStyle: "italic" }}>No meetings yet</div>
                ) : (
                  <ul style={{ paddingLeft: "16px", margin: "6px 0 0 0" }}>
                    {currentContext.recent_meetings.map((title, i) => (
                      <li key={i}>{title}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "#94a3b8", marginTop: "80px", fontStyle: "italic" }}>
              Context will be compiled here once you ask the Copilot.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
