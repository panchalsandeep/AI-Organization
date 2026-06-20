"use client";

import { useEffect, useState, type ReactNode } from "react";
import { getStoredToken } from "./admin-api";

type RoleGuardProps = {
  requiredPermissions: string[];
  children: ReactNode;
};

type JwtPayload = {
  sub?: string;
  permissions?: string[];
  exp?: number;
  [key: string]: unknown;
};

function parseJwt(token: string): JwtPayload | null {
  try {
    const payloadBase64 = token.split(".")[1];
    if (!payloadBase64) {
      return null;
    }

    const payloadJson = decodeURIComponent(
      Array.from(atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")), (c) => {
        return `%${("00" + c.charCodeAt(0).toString(16)).slice(-2)}`;
      }).join("")
    );

    return JSON.parse(payloadJson) as JwtPayload;
  } catch {
    return null;
  }
}

function normalizePermissions(rawPermissions: unknown): string[] {
  if (Array.isArray(rawPermissions)) {
    return rawPermissions.filter(Boolean).map(String);
  }
  if (typeof rawPermissions === "string") {
    return rawPermissions.split(",").map((permission) => permission.trim()).filter(Boolean);
  }
  return [];
}

function hasPermissions(payload: JwtPayload | null, requiredPermissions: string[]): boolean {
  if (!payload) {
    return false;
  }

  if (payload.exp && Date.now() / 1000 > payload.exp) {
    return false;
  }

  const permissions = normalizePermissions(payload.permissions);
  return requiredPermissions.every((permission) => permissions.includes(permission));
}

export default function RoleGuard({ requiredPermissions, children }: RoleGuardProps) {
  const [authorized, setAuthorized] = useState(false);
  const [message, setMessage] = useState("Checking admin permissions...");

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setAuthorized(false);
      setMessage("Admin token is missing. Please log in via the admin login page.");
      return;
    }

    const payload = parseJwt(token);
    if (!payload) {
      setAuthorized(false);
      setMessage("Invalid admin token. Please sign in again.");
      return;
    }

    if (!hasPermissions(payload, requiredPermissions)) {
      setAuthorized(false);
      setMessage(
        `Insufficient permissions. Required: ${requiredPermissions.join(", ")}. ` +
          "Please ensure your role includes these permissions."
      );
      return;
    }

    setAuthorized(true);
  }, [requiredPermissions]);

  if (!authorized) {
    return (
      <section className="card error-card">
        <h2>Access denied</h2>
        <p>{message}</p>
        <p>
          Visit <a href="/admin/login">Admin Login</a> to sign in with valid credentials.
        </p>
      </section>
    );
  }

  return <>{children}</>;
}
