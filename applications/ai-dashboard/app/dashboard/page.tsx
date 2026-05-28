"use client";

import { useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn("NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY is not set");
}

const supabase = createClient(supabaseUrl || "", supabaseAnonKey || "");

export default function DashboardPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [workflowName, setWorkflowName] = useState("example_workflow");
  const [workflowPayload, setWorkflowPayload] = useState("{\n  \"example\": \"payload\"\n}");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runQuery = async () => {
    setLoading(true);
    setError(null);
    try {
      // Invoke Supabase Edge Function named `agent-query` (deploy this function in your Supabase project)
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
    setLoading(true);
    setError(null);
    try {
      const payload = JSON.parse(workflowPayload);

      // Invoke Supabase Edge Function named `workflow-execute`
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
      <section className="hero">
        <h1>AI Operations Dashboard</h1>
        <p>Use this centralized dashboard to query the AI system and execute workflows.</p>
      </section>

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
        <label>
          Payload (JSON)
          <textarea
            rows={6}
            value={workflowPayload}
            onChange={(event) => setWorkflowPayload(event.target.value)}
          />
        </label>
        <button onClick={runWorkflow} disabled={!workflowName || loading}>
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
    </main>
  );
}
