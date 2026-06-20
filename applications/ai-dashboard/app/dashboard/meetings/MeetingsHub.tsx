"use client";

import React, { useState, useEffect } from "react";
import { getJson, postJson, getStoredTenantId } from "../../admin/admin-api";

export default function MeetingsHub() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [selectedMeeting, setSelectedMeeting] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [meetingTitle, setMeetingTitle] = useState("");
  const [audioPath, setAudioPath] = useState("");
  const [duration, setDuration] = useState("0");

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);
    if (tid) {
      fetchMeetings();
    } else {
      setError("Please select a Tenant in the Admin Console first.");
    }
  }, []);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const res = await getJson("/meetings");
      if (res.success) {
        setMeetings(res.meetings);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load meetings list");
    } finally {
      setLoading(false);
    }
  };

  const selectMeeting = async (id: string) => {
    try {
      setLoading(true);
      const res = await getJson(`/meeting/${id}`);
      if (res.success) {
        setSelectedMeeting(res.meeting);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch meeting details");
    } finally {
      setLoading(false);
    }
  };

  const handleProcessMeeting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!meetingTitle) return;

    try {
      setLoading(true);
      setError(null);
      const res = await postJson("/meeting", {
        title: meetingTitle,
        audio_file_path: audioPath || null,
        duration_seconds: duration ? parseInt(duration) : 0,
      });

      if (res.success) {
        setMeetingTitle("");
        setAudioPath("");
        setDuration("0");
        await fetchMeetings();
        if (res.meeting) {
          setSelectedMeeting(res.meeting);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to process meeting audio");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Left panel: Meetings list and process form */}
      <div>
        <div className="card" style={{ marginBottom: "20px" }}>
          <h2>Meetings History</h2>
          {meetings.length === 0 ? (
            <p style={{ color: "#64748b" }}>No meetings recorded.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {meetings.map((m) => (
                <li key={m.id} style={{ marginBottom: "8px" }}>
                  <button
                    id={`meeting-select-${m.id}`}
                    onClick={() => selectMeeting(m.id)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      backgroundColor: selectedMeeting?.id === m.id ? "#e0e7ff" : "transparent",
                      color: selectedMeeting?.id === m.id ? "#3730a3" : "#334155",
                      border: selectedMeeting?.id === m.id ? "1px solid #c7d2fe" : "1px solid transparent",
                      padding: "10px 14px",
                      borderRadius: "8px",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{m.title}</div>
                    <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>
                      Date: {m.date ? new Date(m.date).toLocaleDateString() : "-"} | Duration: {Math.floor(m.duration_seconds / 60)}m
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <h2>Process Recording</h2>
          <form onSubmit={handleProcessMeeting}>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Meeting Title</label>
              <input
                id="meeting-title"
                type="text"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                placeholder="e.g. Q3 Roadmap Review"
                required
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Audio File Path</label>
              <input
                id="meeting-audio-path"
                type="text"
                value={audioPath}
                onChange={(e) => setAudioPath(e.target.value)}
                placeholder="e.g. /tmp/audio.wav"
              />
            </div>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>Duration (seconds)</label>
              <input
                id="meeting-duration"
                type="number"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="e.g. 1800"
              />
            </div>
            <button id="meeting-process-btn" type="submit" disabled={loading} style={{ width: "100%" }}>
              {loading ? "Transcribing & Summarizing..." : "Submit for Processing"}
            </button>
          </form>
        </div>
      </div>

      {/* Right panel: Details of selected meeting */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {error && (
          <div className="card error-card" style={{ padding: "16px", background: "#fef2f2", borderColor: "#fecaca" }}>
            <p style={{ margin: 0, color: "#991b1b" }}>{error}</p>
          </div>
        )}

        {selectedMeeting ? (
          <>
            <div className="card">
              <h1 style={{ margin: 0, fontSize: "26px", color: "#1e1b4b" }}>{selectedMeeting.title}</h1>
              <div style={{ display: "flex", gap: "16px", color: "#64748b", marginTop: "8px", fontSize: "14px" }}>
                <span>Date: <strong>{new Date(selectedMeeting.date).toLocaleString()}</strong></span>
                <span>•</span>
                <span>Duration: <strong>{selectedMeeting.duration_seconds} seconds</strong></span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
              {/* Executive Summary */}
              <div className="card">
                <h2>AI Executive Summary</h2>
                <div style={{ lineHeight: "1.6", color: "#334155", background: "#f8fafc", padding: "16px", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
                  {selectedMeeting.summary}
                </div>
              </div>

              {/* Action items checklist */}
              <div className="card">
                <h2>Action Items Extracted</h2>
                {selectedMeeting.action_items.length === 0 ? (
                  <p style={{ color: "#64748b" }}>No actions extracted.</p>
                ) : (
                  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                    {selectedMeeting.action_items.map((item: any, idx: number) => (
                      <li
                        key={idx}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "12px",
                          padding: "10px 14px",
                          borderRadius: "8px",
                          background: "#f8fafc",
                          border: "1px solid #e2e8f0",
                          marginBottom: "8px",
                        }}
                      >
                        <input
                          type="checkbox"
                          defaultChecked={item.status === "completed"}
                          style={{ width: "16px", height: "16px", cursor: "pointer" }}
                        />
                        <div style={{ flex: 1 }}>
                          <span style={{ fontWeight: 600 }}>{item.task}</span>
                          <div style={{ fontSize: "12px", color: "#64748b" }}>Assignee: {item.assignee}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Transcript text */}
            <div className="card">
              <h2>Full Transcript</h2>
              <div
                style={{
                  maxHeight: "350px",
                  overflowY: "auto",
                  lineHeight: "1.6",
                  background: "#1e293b",
                  color: "#e2e8f0",
                  padding: "20px",
                  borderRadius: "12px",
                  fontFamily: "monospace",
                  whiteSpace: "pre-wrap",
                }}
              >
                {selectedMeeting.transcript_text}
              </div>
            </div>
          </>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "60px", color: "#64748b" }}>
            Select a processed meeting or upload a new recording to view the transcript and AI summary.
          </div>
        )}
      </div>
    </div>
  );
}
