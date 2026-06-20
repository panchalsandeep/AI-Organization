"use client";

import React, { useState, useEffect, useRef } from "react";
import { getJson, postJson, getStoredTenantId, getStoredToken } from "../../admin/admin-api";

export default function CollabHub() {
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [chatRoom, setChatRoom] = useState("general");
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [chatConnected, setChatConnected] = useState(false);

  // Comments state
  const [commentType, setCommentType] = useState("general");
  const [commentId, setCommentId] = useState("board-1");
  const [comments, setComments] = useState<any[]>([]);
  const [newCommentText, setNewCommentText] = useState("");

  // User details (decoded from JWT or stubbed)
  const [user, setUser] = useState({ id: "user-default-1", name: "User" });
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);

    // Resolve user profile from token
    const token = getStoredToken();
    if (token) {
      try {
        // Simple manual split token parser to avoid jwt-decode dependency issues
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = decodeURIComponent(
          window
            .atob(base64)
            .split("")
            .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
            .join("")
        );
        const decoded = JSON.parse(jsonPayload);
        setUser({ id: decoded.sub || "user-default-1", name: decoded.username || "Team Member" });
      } catch (err) {
        console.error("Token decoding error:", err);
      }
    }

    if (tid) {
      loadChatHistory(tid, chatRoom);
      setupChatWebSocket(tid, chatRoom);
      loadComments(tid, commentType, commentId);
    } else {
      setError("Please select a Tenant in the Admin Console first.");
    }

    return () => {
      closeWebSocket();
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const closeWebSocket = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  };

  const setupChatWebSocket = (tid: string, room: string) => {
    closeWebSocket();
    try {
      const wsUrl = `ws://localhost:8000/ws/chat/${tid}/${room}?sender_id=${user.id}&sender_name=${encodeURIComponent(
        user.name
      )}`;
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => setChatConnected(true);
      ws.onclose = () => setChatConnected(false);
      ws.onerror = () => setChatConnected(false);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "new_message") {
          setMessages((prev) => [...prev, data]);
        }
      };
    } catch (err) {
      console.error("Chat WebSocket error:", err);
    }
  };

  const loadChatHistory = async (tid: string, room: string) => {
    try {
      const res = await getJson(`/chat/${room}/history?limit=50`);
      if (res.success) {
        setMessages(res.history);
      }
    } catch (err) {
      console.error("Failed to load chat history", err);
    }
  };

  const switchChatRoom = (room: string) => {
    setChatRoom(room);
    if (tenantId) {
      loadChatHistory(tenantId, room);
      setupChatWebSocket(tenantId, room);
    }
  };

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return;

    socketRef.current.send(newMessage);
    setNewMessage("");
  };

  // Comments features
  const loadComments = async (tid: string, type: string, id: string) => {
    try {
      const res = await getJson(`/comments/${type}/${id}`);
      if (res.success) {
        setComments(res.comments);
      }
    } catch (err) {
      console.error("Failed to load comments", err);
    }
  };

  const handlePostComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommentText) return;

    try {
      const res = await postJson("/comment", {
        resource_type: commentType,
        resource_id: commentId,
        comment_text: newCommentText,
      });

      if (res.success) {
        setNewCommentText("");
        if (tenantId) {
          await loadComments(tenantId, commentType, commentId);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to post comment");
    }
  };

  const switchCommentResource = (type: string, id: string) => {
    setCommentType(type);
    setCommentId(id);
    if (tenantId) {
      loadComments(tenantId, type, id);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Left panel: Real-time Chat Room */}
      <div className="card" style={{ display: "flex", flexDirection: "column", height: "600px", padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ margin: 0 }}>Collaboration Chat</h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "14px", color: "#64748b" }}>
              Room: <strong style={{ color: "#3730a3" }}>#{chatRoom}</strong> | Connection:{" "}
              <strong style={{ color: chatConnected ? "#10b981" : "#ef4444" }}>
                {chatConnected ? "Connected" : "Offline"}
              </strong>
            </p>
          </div>

          {/* Room switcher buttons */}
          <div style={{ display: "flex", gap: "6px" }}>
            {["general", "engineering", "random"].map((rm) => (
              <button
                key={rm}
                onClick={() => switchChatRoom(rm)}
                style={{
                  padding: "4px 8px",
                  fontSize: "12px",
                  backgroundColor: chatRoom === rm ? "#4f46e5" : "#e2e8f0",
                  color: chatRoom === rm ? "#ffffff" : "#475569",
                  borderRadius: "6px",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                #{rm}
              </button>
            ))}
          </div>
        </div>

        {/* Messages body */}
        <div
          style={{
            flex: 1,
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            padding: "16px",
            overflowY: "auto",
            marginBottom: "16px",
          }}
        >
          {messages.length === 0 ? (
            <div style={{ textAlign: "center", color: "#94a3b8", marginTop: "40px" }}>
              No messages in #{chatRoom} yet. Say hello!
            </div>
          ) : (
            messages.map((msg, index) => {
              const isSelf = msg.sender_id === user.id;
              return (
                <div
                  key={msg.id || index}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: isSelf ? "flex-end" : "flex-start",
                    marginBottom: "12px",
                  }}
                >
                  <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "2px" }}>
                    {msg.sender_name}
                  </div>
                  <div
                    style={{
                      background: isSelf ? "#4f46e5" : "#e2e8f0",
                      color: isSelf ? "#ffffff" : "#0f172a",
                      padding: "8px 14px",
                      borderRadius: isSelf ? "12px 12px 0 12px" : "12px 12px 12px 0",
                      maxWidth: "80%",
                      fontSize: "14px",
                      lineHeight: "1.4",
                    }}
                  >
                    {msg.message_text}
                  </div>
                </div>
              );
            })
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input box */}
        <form onSubmit={handleSendChat} style={{ display: "flex", gap: "8px" }}>
          <input
            id="chat-message-input"
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={`Message #${chatRoom}...`}
            style={{ flex: 1 }}
            required
          />
          <button id="chat-send-btn" type="submit" disabled={!chatConnected}>
            Send
          </button>
        </form>
      </div>

      {/* Right panel: Threaded Comments Discussions */}
      <div className="card" style={{ display: "flex", flexDirection: "column", height: "600px", padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ margin: 0 }}>Resource Discussions</h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "14px", color: "#64748b" }}>
              Comments on: <strong>{commentType}:{commentId}</strong>
            </p>
          </div>

          {/* Quick Select Resource type */}
          <div style={{ display: "flex", gap: "6px" }}>
            <button
              onClick={() => switchCommentResource("general", "board-1")}
              style={{
                padding: "4px 8px",
                fontSize: "12px",
                backgroundColor: commentId === "board-1" ? "#312e81" : "#e2e8f0",
                color: commentId === "board-1" ? "#ffffff" : "#475569",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
              }}
            >
              Default
            </button>
            <button
              onClick={() => switchCommentResource("kpi", "kpi-test-id")}
              style={{
                padding: "4px 8px",
                fontSize: "12px",
                backgroundColor: commentType === "kpi" ? "#312e81" : "#e2e8f0",
                color: commentType === "kpi" ? "#ffffff" : "#475569",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
              }}
            >
              KPI Card
            </button>
          </div>
        </div>

        {/* Comments feed */}
        <div
          style={{
            flex: 1,
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            padding: "16px",
            overflowY: "auto",
            marginBottom: "16px",
          }}
        >
          {comments.length === 0 ? (
            <p style={{ color: "#94a3b8", textAlign: "center", marginTop: "40px" }}>
              No comments posted yet. Ask a question or leave feedback!
            </p>
          ) : (
            comments.map((cmt) => (
              <div
                key={cmt.id}
                style={{
                  borderBottom: "1px solid #f1f5f9",
                  paddingBottom: "10px",
                  marginBottom: "10px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", fontWeight: 700, color: "#1e1b4b" }}>
                  <span>{cmt.sender_name}</span>
                  <span style={{ fontWeight: 400, color: "#94a3b8", fontSize: "11px" }}>
                    {cmt.created_at ? new Date(cmt.created_at).toLocaleTimeString() : ""}
                  </span>
                </div>
                <p style={{ margin: "6px 0 0 0", fontSize: "14px", color: "#334155", lineHeight: "1.4" }}>
                  {cmt.comment_text}
                </p>
              </div>
            ))
          )}
        </div>

        {/* Post comment form */}
        <form onSubmit={handlePostComment} style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <textarea
            id="comment-input"
            rows={3}
            value={newCommentText}
            onChange={(e) => setNewCommentText(e.target.value)}
            placeholder={`Leave a comment on ${commentType}:${commentId}...`}
            style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1" }}
            required
          />
          <button id="comment-submit-btn" type="submit">
            Post Comment
          </button>
        </form>
      </div>
    </div>
  );
}
