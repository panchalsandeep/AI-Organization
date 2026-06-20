"use client";

import { useEffect, useState } from "react";
import { getStoredTenantId, saveTenantId } from "./admin-api";

export default function TenantSelector() {
  const [tenantId, setTenantId] = useState<string>("");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    setTenantId(getStoredTenantId() || "");
  }, []);

  function handleSaveTenant() {
    const cleaned = tenantId.trim();
    saveTenantId(cleaned);
    setTenantId(cleaned);
    setMessage(cleaned ? "Tenant context saved locally." : "Tenant context cleared.");
  }

  return (
    <div className="form-row">
      <label>
        Tenant ID
        <input
          type="text"
          value={tenantId}
          onChange={(event) => setTenantId(event.target.value)}
          placeholder="Paste tenant ID for tenant-scoped admin calls"
        />
      </label>
      <button type="button" onClick={handleSaveTenant}>
        Save tenant context
      </button>
      {message ? <p className="status-message">{message}</p> : null}
    </div>
  );
}
