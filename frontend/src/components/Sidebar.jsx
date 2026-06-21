// Sidebar.jsx — Left panel with upload, initialize, clear, logout
// Mirrors streamlit_app.py lines 43-81 (st.sidebar block)
// Developer: vijay_sathappan

import { useRef, useState } from 'react';
import { uploadPdf } from '../api';
import Footer from './Footer';

export default function Sidebar({
  token,
  docInfo,       // { document_id, doc_name, chunks_created } | null
  onDocReady,    // callback(docInfo)
  onClear,       // callback() — mirrors "Clear Document & Reset"
  onLogout,      // callback() — mirrors "Logout"
  addToast,
  totalTokens = 0, // total tokens consumed
}) {
  // Mirrors: uploaded_file = st.file_uploader(...)
  const [file, setFile]           = useState(null);
  const [dragover, setDragover]   = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef();

  // ── Drag & Drop ───────────────────────────────────────────────
  function handleDrop(e) {
    e.preventDefault();
    setDragover(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith('.pdf')) {
      setFile(dropped);
    } else {
      addToast('Only PDF files are supported.', 'error');
    }
  }

  function handleFileChange(e) {
    const chosen = e.target.files[0];
    if (chosen) setFile(chosen);
  }

  // ── Initialize DocMind ────────────────────────────────────────
  // Mirrors: requests.post(f"{API_URL}/upload/pdf", headers=headers, files=files)
  async function handleInitialize() {
    if (!file) return;
    setUploading(true);
    try {
      const data = await uploadPdf(token, file);
      // data = { document_id, chunks_created, filename, message }
      // Mirrors: st.session_state.document_id = data["document_id"]
      onDocReady({
        document_id:    data.document_id,
        doc_name:       data.filename,
        chunks_created: data.chunks_created,
      });
      addToast(`✅ Ready! ${data.chunks_created} chunks indexed.`, 'success');
    } catch (err) {
      // Mirrors: st.error(f"Upload failed: {response.text}")
      addToast(
        err?.response?.data?.detail || 'Upload failed. Check the file and try again.',
        'error'
      );
    } finally {
      setUploading(false);
    }
  }

  // ── Clear ─────────────────────────────────────────────────────
  // Mirrors: st.session_state.document_id = None; st.session_state.doc_name = None; ...
  function handleClear() {
    setFile(null);
    onClear();
  }

  return (
    <aside className="sidebar">
      {/* ── Logo ── */}
      <div className="sidebar-logo">
        <img src="/logo.png" className="logo-img" alt="DocMind AI" />
        <div>
          <h2>DocMind AI</h2>
          <span>Intelligent Q&amp;A</span>
        </div>
      </div>

      <hr className="sidebar-divider" />

      {/* ── Active document status ── */}
      {docInfo && (
        <div className="doc-status">
          <div className="ds-name">📄 {docInfo.doc_name}</div>
          <div className="ds-chunks">{docInfo.chunks_created} chunks indexed</div>
        </div>
      )}

      {/* ── Upload Section ── */}
      {/* Mirrors: st.subheader("📁 Upload Material") */}
      <div>
        <div className="sidebar-section-title">📁 Upload Material</div>

        {/* Drop Zone — mirrors st.file_uploader */}
        {!file ? (
          <div
            id="drop-zone"
            className={`drop-zone${dragover ? ' dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
            onDragLeave={() => setDragover(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <div className="dz-icon">📂</div>
            <div className="dz-text">Drop PDF here or click to browse</div>
            <div className="dz-hint">Supports .pdf files only</div>
          </div>
        ) : (
          /* File chip — mirrors: st.info(f"📄 {uploaded_file.name}") */
          <div className="file-chip">
            <span className="file-icon">📄</span>
            <span>{file.name}</span>
            <button
              id="btn-remove-file"
              style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: '14px' }}
              onClick={() => setFile(null)}
              title="Remove file"
            >
              ✕
            </button>
          </div>
        )}

        {/* Initialize button — mirrors: st.button("Initialize DocMind") */}
        <button
          id="btn-initialize"
          className="btn btn-primary"
          style={{ marginTop: '12px' }}
          disabled={!file || uploading}
          onClick={handleInitialize}
        >
          {uploading ? <><span className="spinner" /> Processing PDF…</> : '🚀 Initialize DocMind'}
        </button>
      </div>

      <hr className="sidebar-divider" />

      {/* ── Token Usage Card ── */}
      <div className="token-usage-section">
        <div className="sidebar-section-title">⚡ LLM Token Usage</div>
        <div className="token-card">
          <div className="token-card-header">
            <span className="token-label">Tokens Consumed</span>
            <span className="token-value">{totalTokens.toLocaleString()}</span>
          </div>
          <div className="token-progress-bar">
            <div 
              className="token-progress-fill" 
              style={{ width: `${Math.min(100, Math.max(2, (totalTokens / 500000) * 100))}%` }} 
            />
          </div>
          <div className="token-card-footer">
            <span>Powered by Groq Cloud</span>
          </div>
        </div>
      </div>

      <hr className="sidebar-divider" />

      {/* ── Actions ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {/* Mirrors: st.button("🗑️ Clear Document & Reset") */}
        <button
          id="btn-clear"
          className="btn btn-danger"
          onClick={handleClear}
          disabled={!docInfo}
        >
          🗑️ Clear Document &amp; Reset
        </button>

        {/* Mirrors: st.button("Logout") */}
        <button
          id="btn-logout"
          className="btn btn-secondary"
          onClick={onLogout}
        >
          🚪 Logout
        </button>
      </div>

      {/* Push footer to bottom */}
      <div style={{ flex: 1 }} />
      <Footer />
    </aside>
  );
}
