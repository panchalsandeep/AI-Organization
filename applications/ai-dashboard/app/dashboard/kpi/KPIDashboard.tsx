"use client";

import React, { useState, useEffect, useRef } from "react";
import { getJson, postJson, getStoredTenantId } from "../../admin/admin-api";

export default function KPIDashboard() {
  const [kpis, setKpis] = useState<any[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [selectedKpi, setSelectedKpi] = useState<any | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [aggregations, setAggregations] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [sensitivity, setSensitivity] = useState<number>(2.0);
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState("Disconnected");

  // Form states
  const [newKpiName, setNewKpiName] = useState("");
  const [newKpiType, setNewKpiType] = useState("number");
  const [newKpiFormula, setNewKpiFormula] = useState("");
  const [newKpiTarget, setNewKpiTarget] = useState("");
  const [logValue, setLogValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);
    if (tid) {
      fetchKpis();
      setupWebSocket(tid);
    } else {
      setError("Please select a Tenant in the Admin Console first.");
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (selectedKpi) {
      fetchAnomalyDetails(selectedKpi.id, sensitivity);
    }
  }, [sensitivity]);

  const fetchKpis = async () => {
    try {
      setLoading(true);
      const res = await getJson("/kpis");
      if (res.success) {
        setKpis(res.kpis);
        if (res.kpis.length > 0 && !selectedKpi) {
          selectKpi(res.kpis[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load KPIs");
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = (tid: string) => {
    try {
      const wsUrl = `ws://localhost:8000/ws/kpi/${tid}`;
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => setConnectionStatus("Connected");
      ws.onclose = () => setConnectionStatus("Disconnected");
      ws.onerror = () => setConnectionStatus("Error");
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLiveEvents((prev) => [data, ...prev.slice(0, 19)]);
        // Auto refresh current KPI if updated
        if (selectedKpi && data.kpi_id === selectedKpi.id) {
          fetchKpiDetails(selectedKpi.id);
        }
      };
    } catch (err) {
      console.error("WebSocket setup error:", err);
    }
  };

  const selectKpi = async (kpi: any) => {
    setSelectedKpi(kpi);
    await fetchKpiDetails(kpi.id);
  };

  const fetchAnomalyDetails = async (kpiId: string, threshold: number) => {
    try {
      const anomalyRes = await getJson(`/kpi/${kpiId}/anomalies?threshold=${threshold}`);
      if (anomalyRes.success) {
        setAnomalies(anomalyRes.anomalies);
      }
    } catch (err) {
      console.error("Failed to load anomalies details:", err);
    }
  };

  const fetchKpiDetails = async (kpiId: string) => {
    try {
      const histRes = await getJson(`/kpi/${kpiId}/history?limit=10`);
      if (histRes.success) {
        setHistory(histRes.history);
      }
      const aggRes = await getJson(`/kpi/${kpiId}/aggregation?interval=day`);
      if (aggRes.success) {
        setAggregations(aggRes.aggregations);
      }
      // Predictions & anomalies
      const forecastRes = await getJson(`/kpi/${kpiId}/forecast?steps=5`);
      if (forecastRes.success) {
        setForecast(forecastRes.forecast);
      }
      await fetchAnomalyDetails(kpiId, sensitivity);
    } catch (err) {
      console.error("Failed to load details for KPI:", kpiId, err);
    }
  };

  const handleCreateKpi = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKpiName) return;

    try {
      setLoading(true);
      const res = await postJson("/kpi", {
        name: newKpiName,
        kpi_type: newKpiType,
        formula: newKpiFormula || null,
        target_value: newKpiTarget ? parseFloat(newKpiTarget) : null,
      });

      if (res.success) {
        setNewKpiName("");
        setNewKpiFormula("");
        setNewKpiTarget("");
        await fetchKpis();
      }
    } catch (err: any) {
      setError(err.message || "Failed to create KPI");
    } finally {
      setLoading(false);
    }
  };

  const handleLogMetric = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedKpi || !logValue) return;

    try {
      setLoading(true);
      const res = await postJson("/kpi/metric", {
        kpi_id: selectedKpi.id,
        value: parseFloat(logValue),
      });

      if (res.success) {
        setLogValue("");
        await fetchKpiDetails(selectedKpi.id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to log metric");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Left panel: list of KPIs & Create */}
      <div>
        <div className="card" style={{ marginBottom: "16px", padding: "16px" }}>
          <h3 style={{ margin: "0 0 12px 0" }}>Connection Status</h3>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: connectionStatus === "Connected" ? "#10b981" : "#ef4444",
                display: "inline-block",
              }}
            />
            <span style={{ fontWeight: 600 }}>{connectionStatus}</span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <h2>KPI List</h2>
          {kpis.length === 0 ? (
            <p style={{ color: "#64748b" }}>No KPIs defined yet.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {kpis.map((k) => (
                <li key={k.id} style={{ marginBottom: "8px" }}>
                  <button
                    id={`kpi-select-${k.id}`}
                    onClick={() => selectKpi(k)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      backgroundColor: selectedKpi?.id === k.id ? "#e0e7ff" : "transparent",
                      color: selectedKpi?.id === k.id ? "#3730a3" : "#334155",
                      border: selectedKpi?.id === k.id ? "1px solid #c7d2fe" : "1px solid transparent",
                      padding: "8px 12px",
                      borderRadius: "8px",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{k.name}</div>
                    <div style={{ fontSize: "12px", color: "#64748b" }}>
                      Type: {k.kpi_type} | Target: {k.target_value ?? "None"}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2>Create KPI</h2>
          <form onSubmit={handleCreateKpi}>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>KPI Name</label>
              <input
                id="kpi-name"
                type="text"
                value={newKpiName}
                onChange={(e) => setNewKpiName(e.target.value)}
                placeholder="e.g. Daily active users"
                required
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Type</label>
              <select
                id="kpi-type"
                value={newKpiType}
                onChange={(e) => setNewKpiType(e.target.value)}
                style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
              >
                <option value="number">Number</option>
                <option value="percentage">Percentage</option>
                <option value="currency">Currency</option>
              </select>
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Formula (Optional)</label>
              <input
                id="kpi-formula"
                type="text"
                value={newKpiFormula}
                onChange={(e) => setNewKpiFormula(e.target.value)}
                placeholder="e.g. users / installations"
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Target Value (Optional)</label>
              <input
                id="kpi-target"
                type="number"
                step="any"
                value={newKpiTarget}
                onChange={(e) => setNewKpiTarget(e.target.value)}
                placeholder="e.g. 500"
              />
            </div>
            <button id="kpi-create-btn" type="submit" disabled={loading} style={{ width: "100%" }}>
              Create KPI
            </button>
          </form>
        </div>
      </div>

      {/* Right Panel: Selected KPI charts, log metric, live activity */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {error && (
          <div className="card error-card" style={{ padding: "16px", background: "#fef2f2", borderColor: "#fecaca" }}>
            <p style={{ margin: 0, color: "#991b1b" }}>{error}</p>
          </div>
        )}

        {selectedKpi ? (
          <>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <div>
                  <h1 style={{ margin: 0, fontSize: "24px", color: "#1e1b4b" }}>{selectedKpi.name}</h1>
                  <p style={{ margin: "4px 0 0 0", color: "#64748b" }}>
                    Type: <strong style={{ color: "#3730a3" }}>{selectedKpi.kpi_type}</strong> | Target:{" "}
                    <strong>{selectedKpi.target_value ?? "None"}</strong>
                  </p>
                </div>

                {/* Log Metric Form inline */}
                <form onSubmit={handleLogMetric} style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <input
                    id="metric-value-input"
                    type="number"
                    step="any"
                    value={logValue}
                    onChange={(e) => setLogValue(e.target.value)}
                    placeholder="Enter value"
                    style={{ width: "130px" }}
                    required
                  />
                  <button id="metric-log-btn" type="submit" style={{ whiteSpace: "nowrap" }}>
                    Log Value
                  </button>
                </form>
              </div>

              {/* Sparkline Chart SVG (Time Series representation with Predictions) */}
              <div style={{ height: "240px", background: "#f8fafc", borderRadius: "12px", border: "1px solid #e2e8f0", padding: "16px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#64748b" }}>Historical Trend & Future Forecast</div>
                  <div style={{ display: "flex", gap: "12px", fontSize: "11px" }}>
                    <span style={{ color: "#4f46e5", fontWeight: 600 }}>● Historical</span>
                    <span style={{ color: "#ea580c", fontWeight: 600 }}>- - Predicted (95% prediction interval)</span>
                  </div>
                </div>
                {history.length < 2 ? (
                  <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center", color: "#94a3b8" }}>
                    Needs at least 2 logged points to plot trend.
                  </div>
                ) : (
                  <div style={{ width: "100%", height: "150px", position: "relative" }}>
                    <svg viewBox="0 0 600 120" style={{ width: "100%", height: "100%", overflow: "visible" }}>
                      {/* Grid lines */}
                      <line x1="0" y1="20" x2="600" y2="20" stroke="#f1f5f9" strokeWidth="1" />
                      <line x1="0" y1="60" x2="600" y2="60" stroke="#f1f5f9" strokeWidth="1" />
                      <line x1="0" y1="100" x2="600" y2="100" stroke="#f1f5f9" strokeWidth="1" />

                      {/* Unified calculations */}
                      {(() => {
                        const histVals = [...history].reverse();
                        
                        // Merge history and forecast values to find min/max range
                        const allValues = [
                          ...histVals.map(v => v.value),
                          ...forecast.map(v => v.value),
                          ...forecast.map(v => v.confidence_upper),
                          ...forecast.map(v => v.confidence_lower)
                        ];
                        
                        const min = Math.min(...allValues);
                        const max = Math.max(...allValues);
                        const range = max - min || 1;
                        
                        const totalPoints = histVals.length + forecast.length;
                        
                        // Calculate coordinates for history
                        const histPointsCoords = histVals.map((v, i) => {
                          const x = (i / (totalPoints - 1)) * 600;
                          const y = 100 - ((v.value - min) / range) * 80;
                          return { x, y, val: v.value, id: v.id };
                        });
                        
                        // Calculate coordinates for forecast
                        const forecastPointsCoords = forecast.map((f, i) => {
                          const idx = histVals.length + i;
                          const x = (idx / (totalPoints - 1)) * 600;
                          const y = 100 - ((f.value - min) / range) * 80;
                          const yUpper = 100 - ((f.confidence_upper - min) / range) * 80;
                          const yLower = 100 - ((f.confidence_lower - min) / range) * 80;
                          return { x, y, yUpper, yLower, val: f.value };
                        });

                        const histPointsStr = histPointsCoords.map(p => `${p.x},${p.y}`).join(" ");
                        
                        // Joint line from last historical point to first forecast
                        let jointPointsStr = "";
                        if (histPointsCoords.length > 0 && forecastPointsCoords.length > 0) {
                          const lastHist = histPointsCoords[histPointsCoords.length - 1];
                          jointPointsStr = `${lastHist.x},${lastHist.y} ` + forecastPointsCoords.map(p => `${p.x},${p.y}`).join(" ");
                        }

                        // Shaded confidence interval region polygon coordinates
                        let confidenceAreaPoints = "";
                        if (histPointsCoords.length > 0 && forecastPointsCoords.length > 0) {
                          const lastHist = histPointsCoords[histPointsCoords.length - 1];
                          const upperPath = forecastPointsCoords.map(p => `${p.x},${p.yUpper}`);
                          const lowerPath = [...forecastPointsCoords].reverse().map(p => `${p.x},${p.yLower}`);
                          
                          // Form a closed loop starting and ending at the last historical point
                          confidenceAreaPoints = [
                            `${lastHist.x},${lastHist.y}`,
                            ...upperPath,
                            ...lowerPath,
                            `${lastHist.x},${lastHist.y}`
                          ].join(" ");
                        }

                        return (
                          <>
                            {/* Shaded Confidence Area */}
                            {confidenceAreaPoints && (
                              <polygon
                                points={confidenceAreaPoints}
                                fill="rgba(234, 88, 12, 0.12)"
                                stroke="none"
                              />
                            )}

                            {/* Historical line */}
                            <polyline
                              fill="none"
                              stroke="#4f46e5"
                              strokeWidth="3"
                              points={histPointsStr}
                            />

                            {/* Predicted line (dashed) */}
                            {jointPointsStr && (
                              <polyline
                                fill="none"
                                stroke="#ea580c"
                                strokeWidth="2.5"
                                strokeDasharray="5,5"
                                points={jointPointsStr}
                              />
                            )}

                            {/* Historical dot circles */}
                            {histPointsCoords.map((p) => (
                              <circle
                                key={p.id}
                                cx={p.x}
                                cy={p.y}
                                r="4"
                                fill="#ffffff"
                                stroke="#4f46e5"
                                strokeWidth="2"
                              />
                            ))}

                            {/* Forecast dot circles */}
                            {forecastPointsCoords.map((p, idx) => (
                              <circle
                                key={idx}
                                cx={p.x}
                                cy={p.y}
                                r="4"
                                fill="#ffffff"
                                stroke="#ea580c"
                                strokeWidth="2"
                              />
                            ))}
                          </>
                        );
                      })()}
                    </svg>
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
              {/* History Table */}
              <div className="card">
                <h2>Recent Entries</h2>
                {history.length === 0 ? (
                  <p style={{ color: "#64748b" }}>No entries logged yet.</p>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((h) => (
                        <tr key={h.id}>
                          <td>{h.timestamp ? new Date(h.timestamp).toLocaleString() : "-"}</td>
                          <td style={{ fontWeight: 600 }}>{h.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Aggregation Table */}
              <div className="card">
                <h2>Daily Aggregations</h2>
                {aggregations.length === 0 ? (
                  <p style={{ color: "#64748b" }}>No aggregated data available.</p>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Day</th>
                        <th>Avg Value</th>
                        <th>Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aggregations.map((a, idx) => (
                        <tr key={idx}>
                          <td>{a.time_bucket ? new Date(a.time_bucket).toLocaleDateString() : "-"}</td>
                          <td style={{ fontWeight: 600 }}>{a.avg_value.toFixed(2)}</td>
                          <td>{a.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
            {/* Anomaly Detection and Sensitivity Threshold Controls */}
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2>Anomaly Detection (Predictive Engine)</h2>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span style={{ fontSize: "14px", fontWeight: 600, color: "#64748b" }}>
                    Z-Score Sensitivity: <strong>{sensitivity.toFixed(1)} σ</strong>
                  </span>
                  <input
                    id="anomaly-sensitivity-slider"
                    type="range"
                    min="1.0"
                    max="3.5"
                    step="0.1"
                    value={sensitivity}
                    onChange={(e) => setSensitivity(parseFloat(e.target.value))}
                    style={{ width: "150px", margin: 0, padding: 0, height: "8px", cursor: "pointer" }}
                  />
                </div>
              </div>

              {anomalies.length === 0 ? (
                <p style={{ color: "#059669", fontWeight: 600, background: "#d1fae5", padding: "10px 16px", borderRadius: "10px", margin: 0 }}>
                  ✅ No anomalies detected in history with the current sensitivity threshold.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div style={{ background: "#fff1f2", border: "1px solid #fecaca", padding: "10px 16px", borderRadius: "10px", color: "#991b1b", fontWeight: 600, marginBottom: "6px" }}>
                    ⚠️ {anomalies.length} anomalous data points flagged in metric history!
                  </div>
                  <div style={{ maxHeight: "200px", overflowY: "auto" }}>
                    <table style={{ margin: 0 }}>
                      <thead>
                        <tr style={{ background: "#ffe4e6" }}>
                          <th>Timestamp</th>
                          <th>Value</th>
                          <th>Z-Score</th>
                          <th>Threshold</th>
                        </tr>
                      </thead>
                      <tbody>
                        {anomalies.map((anom, i) => (
                          <tr key={i} style={{ background: i % 2 === 0 ? "#fff5f5" : "#ffffff" }}>
                            <td>{new Date(anom.timestamp).toLocaleString()}</td>
                            <td style={{ fontWeight: 700, color: "#e11d48" }}>{anom.value}</td>
                            <td style={{ fontWeight: 600, color: "#991b1b" }}>{anom.z_score} σ</td>
                            <td>{anom.threshold} σ</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>
            Select or define a KPI from the left panel to begin.
          </div>
        )}

        {/* Live WS metric logs ticker */}
        <div className="card">
          <h2>Live Stream Metric Ticker (WebSocket)</h2>
          {liveEvents.length === 0 ? (
            <p style={{ color: "#94a3b8", fontStyle: "italic" }}>Listening for live events... values logged above will push updates instantly.</p>
          ) : (
            <div style={{ maxHeight: "200px", overflowY: "auto" }}>
              {liveEvents.map((ev, index) => (
                <div
                  key={index}
                  style={{
                    padding: "8px 12px",
                    borderRadius: "8px",
                    background: ev.anomaly_flagged || ev.alert_triggered ? "#fef2f2" : "#f0fdf4",
                    border: ev.anomaly_flagged || ev.alert_triggered ? "1px solid #fecaca" : "1px solid #bbf7d0",
                    color: ev.anomaly_flagged || ev.alert_triggered ? "#991b1b" : "#15803d",
                    marginBottom: "8px",
                    fontSize: "14px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                  }}
                >
                  <span>
                    <strong>Event</strong>: {ev.event} | KPI ID: {ev.kpi_id.substring(0, 8)}... | Value:{" "}
                    <strong>{ev.value}</strong>
                    {ev.anomaly_flagged && (
                      <span style={{ fontWeight: 700, color: "#e11d48", background: "#ffe4e6", padding: "2px 6px", borderRadius: "6px", marginLeft: "10px", fontSize: "12px" }}>
                        ⚠️ Anomaly Detected! (Z-Score: {ev.z_score} σ)
                      </span>
                    )}
                  </span>
                  {ev.alert_triggered && (
                    <span style={{ fontWeight: 700 }}>⚠️ Alert: Target Threshold Not Met!</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
