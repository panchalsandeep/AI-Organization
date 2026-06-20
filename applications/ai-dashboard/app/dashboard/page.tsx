"use client";

import { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";
import Link from "next/link";
import KPIDashboard from "./kpi/KPIDashboard";
import MeetingsHub from "./meetings/MeetingsHub";
import CollabHub from "./collaboration/CollabHub";
import IntegrationsPanel from "./integrations/IntegrationsPanel";
import AutomationPanel from "./automation/AutomationPanel";
import CopilotPanel from "./copilot/CopilotPanel";
import DecisionPortal from "./decision/DecisionPortal";
import WikiPortal from "./wiki/WikiPortal";
import { getStoredTenantId } from "../admin/admin-api";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null;

export default function DashboardPage() {
  // Tabs: 'copilot', 'integrations', 'automation', 'assistant', 'kpis', 'meetings', 'collab'
  const [activeTab, setActiveTab] = useState("copilot");
  const [tenantId, setTenantId] = useState<string | null>(null);

  // Original Assistant tab states
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [workflowName, setWorkflowName] = useState("example_workflow");
  const [workflowPayload, setWorkflowPayload] = useState("{\n  \"example\": \"payload\"\n}");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTenantId(getStoredTenantId());
  }, []);

  const runQuery = async () => {
    if (!supabase) {
      setError("Supabase is not configured. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const { data, error } = await supabase.functions.invoke("agent-query", {
        body: JSON.stringify({ query }),
      });

      if (error) throw error;
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const runWorkflow = async () => {
    if (!supabase) {
      setError("Supabase is not configured. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload = JSON.parse(workflowPayload);
      const { data, error } = await supabase.functions.invoke("workflow-execute", {
        body: JSON.stringify({ workflow_name: workflowName, payload }),
      });

      if (error) throw error;
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-container">
      {/* Header and Tenant ID Banner */}
      <section className="hero" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1>AI Operations Dashboard</h1>
          <p>Unified enterprise intelligence, analytics, and operational tracking.</p>
        </div>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <Link href="/admin">
            <button style={{ backgroundColor: "#312e81" }}>Admin Console</button>
          </Link>
          <Link href="/">
            <button style={{ backgroundColor: "#475569" }}>Home</button>
          </Link>
        </div>
      </section>

      {/* Tenant Indicator */}
      <div
        className="card"
        style={{
          padding: "12px 20px",
          background: tenantId ? "#f0fdf4" : "#fffbeb",
          borderColor: tenantId ? "#bbf7d0" : "#fef3c7",
          color: tenantId ? "#15803d" : "#b45309",
          marginBottom: "24px",
          fontWeight: 600,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span>
          {tenantId ? (
            <>Active Tenant Context: <strong>{tenantId}</strong></>
          ) : (
            <>⚠️ No Active Tenant Selected. Please configure context in the Admin Console.</>
          )}
        </span>
        <Link href="/admin/tenants" style={{ color: "#3730a3", fontSize: "14px" }}>
          Manage Tenants →
        </Link>
      </div>

      {/* Tabs Selector Navigation */}
      <div className="admin-nav" style={{ marginBottom: "24px" }}>
        <button
          onClick={() => setActiveTab("copilot")}
          style={{
            background: activeTab === "copilot" ? "#4f46e5" : "transparent",
            color: activeTab === "copilot" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          🤖 AI Copilot
        </button>
        <button
          onClick={() => setActiveTab("integrations")}
          style={{
            background: activeTab === "integrations" ? "#4f46e5" : "transparent",
            color: activeTab === "integrations" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          🔌 Connectors
        </button>
        <button
          onClick={() => setActiveTab("automation")}
          style={{
            background: activeTab === "automation" ? "#4f46e5" : "transparent",
            color: activeTab === "automation" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          ⚙️ n8n Automation
        </button>
        <button
          onClick={() => setActiveTab("kpis")}
          style={{
            background: activeTab === "kpis" ? "#4f46e5" : "transparent",
            color: activeTab === "kpis" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          📈 KPI Analytics (Live)
        </button>
        <button
          onClick={() => setActiveTab("meetings")}
          style={{
            background: activeTab === "meetings" ? "#4f46e5" : "transparent",
            color: activeTab === "meetings" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          🎙️ Meetings Intelligence
        </button>
        <button
          onClick={() => setActiveTab("collab")}
          style={{
            background: activeTab === "collab" ? "#4f46e5" : "transparent",
            color: activeTab === "collab" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          💬 Team Collaboration
        </button>
        <button
          onClick={() => setActiveTab("decision")}
          style={{
            background: activeTab === "decision" ? "#4f46e5" : "transparent",
            color: activeTab === "decision" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          ⚖️ Decision Portal
        </button>
        <button
          onClick={() => setActiveTab("wiki")}
          style={{
            background: activeTab === "wiki" ? "#4f46e5" : "transparent",
            color: activeTab === "wiki" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          📖 Knowledge Base
        </button>
        <button
          onClick={() => setActiveTab("assistant")}
          style={{
            background: activeTab === "assistant" ? "#4f46e5" : "transparent",
            color: activeTab === "assistant" ? "#ffffff" : "#4f46e5",
            border: "1px solid #4f46e5",
            padding: "8px 16px",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          🤖 Edge Functions
        </button>
      </div>

      {/* RENDER DYNAMIC TAB VIEWS */}
      {activeTab === "copilot" && <CopilotPanel />}

      {activeTab === "integrations" && <IntegrationsPanel />}

      {activeTab === "automation" && <AutomationPanel />}

      {activeTab === "assistant" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <section className="card">
            <h2>AI Query</h2>
            <textarea
              rows={4}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Enter your query here"
            />
            <button onClick={runQuery} disabled={!query || loading}>
              {loading ? "Running..." : "Run Query"}
            </button>
          </section>

          <section className="card">
            <h2>Workflow Execution</h2>
            <label>
              Workflow name
              <input
                value={workflowName}
                onChange={(event) => setWorkflowName(event.target.value)}
              />
            </label>
            <label style={{ marginTop: "12px", display: "block" }}>
              Payload (JSON)
              <textarea
                rows={6}
                value={workflowPayload}
                onChange={(event) => setWorkflowPayload(event.target.value)}
              />
            </label>
            <button onClick={runWorkflow} disabled={!workflowName || loading} style={{ marginTop: "12px" }}>
              {loading ? "Executing..." : "Execute Workflow"}
            </button>
          </section>

          {error ? (
            <section className="card error-card">
              <h2>Error</h2>
              <pre>{error}</pre>
            </section>
          ) : null}

          {result ? (
            <section className="card result-card">
              <h2>Result</h2>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </section>
          ) : null}
        </div>
      )}

      {activeTab === "kpis" && <KPIDashboard />}

      {activeTab === "meetings" && <MeetingsHub />}

      {activeTab === "collab" && <CollabHub />}

      {activeTab === "decision" && <DecisionPortal />}
      {activeTab === "wiki" && <WikiPortal />}
    </main>
  );
}
