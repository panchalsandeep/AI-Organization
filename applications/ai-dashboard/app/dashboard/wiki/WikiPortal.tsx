"use client";

import React, { useState, useEffect } from "react";
import { getJson, postJson, getStoredTenantId } from "../../admin/admin-api";

interface WikiPage {
  id: string;
  title: string;
  slug: string;
  content: string;
  tags: string[];
  version: number;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
}

interface WikiVersion {
  id: string;
  title: string;
  content: string;
  version: number;
  updated_by: string;
  created_at: string | null;
}

interface VectorRecommendation {
  title: string;
  wiki_page_id: string;
  similarity: number;
}

export default function WikiPortal() {
  const [pages, setPages] = useState<WikiPage[]>([]);
  const [selectedPage, setSelectedPage] = useState<WikiPage | null>(null);
  const [history, setHistory] = useState<WikiVersion[]>([]);
  const [recommendations, setRecommendations] = useState<VectorRecommendation[]>([]);
  const [tenantId, setTenantId] = useState<string | null>(null);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  // Create/Edit View Mode State
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Form Field States
  const [formTitle, setFormTitle] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [formContent, setFormContent] = useState("");
  const [formTags, setFormTags] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const tid = getStoredTenantId();
    setTenantId(tid);
    if (tid) {
      fetchPages();
    } else {
      setError("Please select a Tenant in the Admin Console first.");
    }
  }, []);

  const fetchPages = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getJson("/wiki/pages");
      if (res.success) {
        setPages(res.pages);
        if (res.pages.length > 0 && !selectedPage) {
          handleSelectPage(res.pages[0]);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch wiki pages");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPage = async (page: WikiPage) => {
    setSelectedPage(page);
    setIsCreating(false);
    setIsEditing(false);
    setShowHistory(false);
    setSuccessMsg(null);
    setError(null);

    // Fetch related content recommendations & history
    await Promise.all([
      fetchHistory(page.id),
      fetchRecommendations(page.title)
    ]);
  };

  const fetchHistory = async (pageId: string) => {
    try {
      const res = await getJson(`/wiki/page/${pageId}/history`);
      if (res.success) {
        setHistory(res.history);
      }
    } catch (err) {
      console.error("Failed to fetch wiki version history", err);
    }
  };

  const fetchRecommendations = async (title: string) => {
    try {
      const res = await getJson(`/wiki/search?q=${encodeURIComponent(title)}`);
      if (res.success) {
        // Filter out the active page from the recommendation list
        const filtered = (res.recommendations || []).filter(
          (rec: VectorRecommendation) => rec.wiki_page_id !== selectedPage?.id
        );
        setRecommendations(filtered);
      }
    } catch (err) {
      console.error("Failed to fetch vector recommendation similarities", err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setIsSearching(false);
      await fetchPages();
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setIsSearching(true);
      const res = await getJson(`/wiki/search?q=${encodeURIComponent(searchQuery)}`);
      if (res.success) {
        setPages(res.results || []);
        setRecommendations(res.recommendations || []);
      }
    } catch (err: any) {
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleStartCreate = () => {
    setIsCreating(true);
    setIsEditing(false);
    setShowHistory(false);
    setFormTitle("");
    setFormSlug("");
    setFormContent("");
    setFormTags("");
    setError(null);
    setSuccessMsg(null);
  };

  const handleStartEdit = () => {
    if (!selectedPage) return;
    setIsEditing(true);
    setIsCreating(false);
    setShowHistory(false);
    setFormTitle(selectedPage.title);
    setFormSlug(selectedPage.slug);
    setFormContent(selectedPage.content);
    setFormTags(selectedPage.tags.join(", "));
    setError(null);
    setSuccessMsg(null);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim() || !formContent.trim()) {
      setError("Title and Content are required.");
      return;
    }

    const tagsArray = formTags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    try {
      setLoading(true);
      setError(null);
      const res = await postJson("/wiki", {
        title: formTitle,
        slug: formSlug.trim() || null,
        content: formContent,
        tags: tagsArray
      });

      if (res.success) {
        setSuccessMsg(`Wiki page '${formTitle}' created!`);
        setIsCreating(false);
        await fetchPages();
        if (res.page) {
          handleSelectPage(res.page);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to create wiki page");
    } finally {
      setLoading(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPage || !formTitle.trim() || !formContent.trim()) {
      setError("Title and Content are required.");
      return;
    }

    const token = typeof window !== "undefined" ? window.localStorage.getItem("AI_OPS_ADMIN_TOKEN") : null;
    const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    const tagsArray = formTags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    try {
      setLoading(true);
      setError(null);

      const payload = {
        title: formTitle,
        slug: formSlug.trim() || null,
        content: formContent,
        tags: tagsArray
      };

      const res = await fetch(`http://localhost:8000/wiki/page/${selectedPage.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId || "",
          ...authHeaders
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || "Failed to update page");
      }

      const data = await res.json();
      if (data.success) {
        setSuccessMsg("Wiki page updated successfully.");
        setIsEditing(false);
        setSelectedPage(data.page);
        const updatedPages = pages.map((p) => (p.id === selectedPage.id ? data.page : p));
        setPages(updatedPages);
        await Promise.all([
          fetchHistory(data.page.id),
          fetchRecommendations(data.page.title)
        ]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to update wiki page");
    } finally {
      setLoading(false);
    }
  };

  const executeDelete = async () => {
    if (!selectedPage || !confirm(`Are you sure you want to delete '${selectedPage.title}'?`)) return;

    const token = typeof window !== "undefined" ? window.localStorage.getItem("AI_OPS_ADMIN_TOKEN") : null;
    const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      setLoading(true);
      setError(null);

      const res = await fetch(`http://localhost:8000/wiki/page/${selectedPage.id}`, {
        method: "DELETE",
        headers: {
          "X-Tenant-ID": tenantId || "",
          ...authHeaders
        }
      });

      if (!res.ok) {
        throw new Error("Failed to delete page");
      }

      setSuccessMsg("Wiki page deleted.");
      setSelectedPage(null);
      await fetchPages();
    } catch (err: any) {
      setError(err.message || "Failed to delete page");
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (versionSnap: WikiVersion) => {
    if (!selectedPage || !confirm(`Rollback to version ${versionSnap.version}?`)) return;

    const token = typeof window !== "undefined" ? window.localStorage.getItem("AI_OPS_ADMIN_TOKEN") : null;
    const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      setLoading(true);
      setError(null);

      const payload = {
        title: versionSnap.title,
        slug: selectedPage.slug,
        content: versionSnap.content,
        tags: selectedPage.tags
      };

      const res = await fetch(`http://localhost:8000/wiki/page/${selectedPage.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": tenantId || "",
          ...authHeaders
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("Rollback failed");
      }

      const data = await res.json();
      if (data.success) {
        setSuccessMsg(`Restored to version ${versionSnap.version}`);
        setSelectedPage(data.page);
        const updated = pages.map((p) => (p.id === selectedPage.id ? data.page : p));
        setPages(updated);
        await fetchHistory(data.page.id);
        setShowHistory(false);
      }
    } catch (err: any) {
      setError(err.message || "Rollback failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRecommendationClick = (recId: string) => {
    const matched = pages.find((p) => p.id === recId);
    if (matched) {
      handleSelectPage(matched);
    }
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "24px", minHeight: "600px" }}>
      {/* Sidebar - Search and Articles list */}
      <div>
        <div className="card" style={{ padding: "16px", marginBottom: "16px" }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#475569" }}>Documentation Search</h3>
          <form onSubmit={handleSearch} style={{ display: "flex", gap: "8px" }}>
            <input
              id="wiki-search-input"
              type="text"
              placeholder="Search wiki..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ padding: "8px 12px", fontSize: "13px", margin: 0 }}
            />
            <button
              id="wiki-search-btn"
              type="submit"
              style={{
                margin: 0,
                padding: "8px 12px",
                fontSize: "13px",
                background: "#4f46e5",
                fontWeight: 600,
                borderRadius: "10px"
              }}
            >
              Go
            </button>
          </form>
          {isSearching && (
            <button
              onClick={() => {
                setSearchQuery("");
                setIsSearching(false);
                fetchPages();
              }}
              style={{
                width: "100%",
                padding: "6px",
                marginTop: "8px",
                fontSize: "12px",
                background: "#64748b",
                borderRadius: "8px"
              }}
            >
              Clear Search
            </button>
          )}
        </div>

        <button
          id="wiki-new-btn"
          onClick={handleStartCreate}
          style={{
            width: "100%",
            background: "linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)",
            borderRadius: "12px",
            marginTop: 0,
            marginBottom: "16px",
            boxShadow: "0 4px 12px rgba(79, 70, 229, 0.2)"
          }}
        >
          ➕ New Article
        </button>

        <div className="card">
          <h2>Articles</h2>
          {loading && pages.length === 0 ? (
            <p>Loading wiki pages...</p>
          ) : pages.length === 0 ? (
            <p style={{ color: "#64748b" }}>No articles found.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {pages.map((p) => (
                <li key={p.id} style={{ marginBottom: "10px" }}>
                  <button
                    id={`wiki-select-${p.id}`}
                    onClick={() => handleSelectPage(p)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      backgroundColor: selectedPage?.id === p.id ? "#e0e7ff" : "transparent",
                      color: selectedPage?.id === p.id ? "#3730a3" : "#334155",
                      border: selectedPage?.id === p.id ? "1px solid #c7d2fe" : "1px solid #cbd5e1",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      marginTop: 0
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "14px" }}>{p.title}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "6px", fontSize: "11px", color: "#64748b" }}>
                      <span>v{p.version}</span>
                      <span>slug: {p.slug}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Main Workspace Area */}
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

        {isCreating || isEditing ? (
          <div className="card">
            <h2>{isCreating ? "Create New Article" : "Edit Wiki Article"}</h2>
            <form onSubmit={isCreating ? handleCreateSubmit : handleEditSubmit}>
              <div style={{ marginBottom: "14px" }}>
                <label style={{ margin: 0, fontSize: "14px" }}>Title</label>
                <input
                  id="wiki-form-title"
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="e.g. SOC 2 Access Control Guidelines"
                  required
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ margin: 0, fontSize: "14px" }}>Slug (Optional, auto-generated from title)</label>
                <input
                  id="wiki-form-slug"
                  type="text"
                  value={formSlug}
                  onChange={(e) => setFormSlug(e.target.value)}
                  placeholder="e.g. soc2-access-control"
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ margin: 0, fontSize: "14px" }}>Content</label>
                <textarea
                  id="wiki-form-content"
                  rows={12}
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  placeholder="Wiki content (Markdown/Plaintext)..."
                  required
                />
              </div>

              <div style={{ marginBottom: "14px" }}>
                <label style={{ margin: 0, fontSize: "14px" }}>Tags (comma-separated)</label>
                <input
                  id="wiki-form-tags"
                  type="text"
                  value={formTags}
                  onChange={(e) => setFormTags(e.target.value)}
                  placeholder="security, compliance, infrastructure"
                />
              </div>

              <div style={{ display: "flex", gap: "12px", marginTop: "24px" }}>
                <button
                  id="wiki-form-submit"
                  type="submit"
                  disabled={loading}
                  style={{ flex: 1, marginTop: 0, background: "#4f46e5" }}
                >
                  {loading ? "Saving..." : "Save Article"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsCreating(false);
                    setIsEditing(false);
                  }}
                  style={{ flex: 1, marginTop: 0, background: "#64748b" }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        ) : selectedPage ? (
          <>
            {/* Header controls card */}
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h1 style={{ margin: 0, fontSize: "24px", color: "#1e1b4b" }}>{selectedPage.title}</h1>
                  <div style={{ color: "#64748b", fontSize: "13px", marginTop: "6px" }}>
                    Version <strong>{selectedPage.version}</strong> | Created by <strong>{selectedPage.created_by}</strong> on {selectedPage.created_at ? new Date(selectedPage.created_at).toLocaleString() : "-"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    id="wiki-edit-btn"
                    onClick={handleStartEdit}
                    style={{ backgroundColor: "#4f46e5", marginTop: 0, padding: "8px 14px", fontSize: "14px" }}
                  >
                    ✏️ Edit
                  </button>
                  <button
                    id="wiki-history-btn"
                    onClick={() => setShowHistory(!showHistory)}
                    style={{ backgroundColor: "#0284c7", marginTop: 0, padding: "8px 14px", fontSize: "14px" }}
                  >
                    ⏱️ History
                  </button>
                  <button
                    id="wiki-delete-btn"
                    onClick={executeDelete}
                    style={{ backgroundColor: "#dc2626", marginTop: 0, padding: "8px 14px", fontSize: "14px" }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>

            {showHistory ? (
              <div className="card">
                <h2>Revision History</h2>
                {history.length === 0 ? (
                  <p>No revision log available.</p>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                    {history.map((hist) => (
                      <div
                        key={hist.id}
                        style={{
                          border: "1px solid #cbd5e1",
                          borderRadius: "12px",
                          padding: "16px",
                          background: "#f8fafc",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center"
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 700, color: "#1e1b4b" }}>Version {hist.version} - {hist.title}</div>
                          <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>
                            Modified by <strong>{hist.updated_by}</strong> on {hist.created_at ? new Date(hist.created_at).toLocaleString() : "-"}
                          </div>
                        </div>
                        {hist.version < selectedPage.version && (
                          <button
                            id={`wiki-rollback-${hist.version}`}
                            onClick={() => handleRollback(hist)}
                            style={{
                              marginTop: 0,
                              padding: "6px 12px",
                              fontSize: "12.5px",
                              background: "#ea580c"
                            }}
                          >
                            Restore Version
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "24px" }}>
                {/* Article Reader Pane */}
                <div className="card" style={{ marginBottom: 0, minHeight: "350px" }}>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "16px" }}>
                    {selectedPage.tags.length === 0 ? (
                      <span style={{ color: "#94a3b8", fontSize: "12px" }}>No tags</span>
                    ) : (
                      selectedPage.tags.map((tag, index) => (
                        <span
                          key={index}
                          style={{
                            background: "#e0e7ff",
                            color: "#4f46e5",
                            padding: "3px 8px",
                            borderRadius: "12px",
                            fontSize: "11px",
                            fontWeight: 700
                          }}
                        >
                          #{tag}
                        </span>
                      ))
                    )}
                  </div>
                  <hr style={{ border: 0, height: "1px", background: "#e2e8f0", marginBottom: "20px" }} />
                  <div
                    style={{
                      fontSize: "15px",
                      lineHeight: "1.7",
                      color: "#334155",
                      whiteSpace: "pre-wrap",
                      fontFamily: "Inter, sans-serif"
                    }}
                  >
                    {selectedPage.content}
                  </div>
                </div>

                {/* Recommendations Pane */}
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <div className="card" style={{ marginBottom: 0 }}>
                    <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#3730a3", fontWeight: 700 }}>
                      ⚡ Related (Vector Similarity)
                    </h3>
                    {recommendations.length === 0 ? (
                      <p style={{ color: "#94a3b8", fontSize: "12.5px", margin: 0 }}>No recommendations found</p>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {recommendations.map((rec, i) => (
                          <div
                            key={i}
                            style={{
                              border: "1px solid #e2e8f0",
                              borderRadius: "10px",
                              padding: "10px",
                              background: "#f8fafc"
                            }}
                          >
                            <div style={{ fontWeight: 600, fontSize: "13px", color: "#334155" }}>
                              {rec.title}
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" }}>
                              <span style={{ fontSize: "10px", color: "#059669", background: "#d1fae5", padding: "1px 5px", borderRadius: "4px", fontWeight: 700 }}>
                                {(rec.similarity * 100).toFixed(0)}% Match
                              </span>
                              {rec.wiki_page_id && (
                                <button
                                  onClick={() => handleRecommendationClick(rec.wiki_page_id)}
                                  style={{
                                    marginTop: 0,
                                    padding: "2px 8px",
                                    fontSize: "11px",
                                    background: "#3730a3",
                                    borderRadius: "6px"
                                  }}
                                >
                                  Read
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="card" style={{ textAlign: "center", padding: "80px 24px", color: "#64748b" }}>
            <h2>No Article Selected</h2>
            <p>Select an article from the list or create a new one to begin editing or viewing documentation.</p>
          </div>
        )}
      </div>
    </div>
  );
}
