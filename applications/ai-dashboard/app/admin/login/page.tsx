"use client";

import { useState, FormEvent } from "react";
import { saveToken } from "../admin-api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminLoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const body = new URLSearchParams();
      body.append("username", username);
      body.append("password", password);

      const response = await fetch(`${API_BASE}/auth/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || JSON.stringify(data));
      }

      saveToken(data.access_token);
      setMessage("Login successful. Token stored locally.");
      setUsername("");
      setPassword("");
    } catch (error: any) {
      setMessage(`Login failed: ${error.message || String(error)}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-container">
      <section className="hero">
        <h1>Admin Login</h1>
        <p>Sign in to obtain an API token for tenant, RBAC, audit, and compliance administration.</p>
      </section>

      <section className="card login-card">
        <form onSubmit={handleLogin}>
          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        {message ? <p className="status-message">{message}</p> : null}
      </section>
    </main>
  );
}
