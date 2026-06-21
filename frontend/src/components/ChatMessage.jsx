// ChatMessage.jsx — Renders a single chat message bubble
// Mirrors streamlit_app.py lines 99-105 (chat_message user/assistant with cache badge)
// Developer: vijay_sathappan

import { useState } from 'react';

export default function ChatMessage({ role, text, fromCache, sourcesUsed, sources }) {
  const isUser = role === 'user';
  const [activeSource, setActiveSource] = useState(null);

  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      {/* ── Avatar ── */}
      <div className="message-avatar">
        {isUser ? '👤' : '🧠'}
      </div>

      {/* ── Bubble ── */}
      <div className="message-body">
        {/* User queries are styled in distinct compact blocks. 
            Assistant responses flow natively like Claude. */}
        {isUser ? (
          <div className="message-bubble">
            {text}
          </div>
        ) : (
          <div className="assistant-message-content">
            {/* ── Perplexity-style Citation Sources (above text) ── */}
            {!isUser && sources && sources.length > 0 && (
              <div className="message-sources-section">
                <div className="sources-sec-title">
                  <span className="sources-icon">🔍</span>
                  <span>Sources</span>
                </div>
                <div className="sources-grid">
                  {sources.map((src, sIdx) => (
                    <div 
                      key={sIdx} 
                      className="source-card" 
                      onClick={() => setActiveSource({ ...src, index: sIdx + 1 })}
                      title="Click to view full chunk text"
                    >
                      <div className="source-card-header">
                        <span className="source-index">{sIdx + 1}</span>
                        <span className="source-title">Page {src.page_number}</span>
                      </div>
                      <div className="source-card-snippet">
                        {src.chunk_text}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Response body */}
            <div className="answer-text">
              {text}
            </div>

            {/* Cache badge — mirrors: st.caption("⚡ Served from cache") */}
            {fromCache && (
              <div className="cache-badge">
                ⚡ Served from cache
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Source Details Overlay Modal ── */}
      {activeSource && (
        <div className="source-modal-overlay" onClick={() => setActiveSource(null)}>
          <div className="source-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="source-modal-header">
              <span className="modal-source-badge">Source {activeSource.index}</span>
              <h3>Page {activeSource.page_number} (Chunk {activeSource.chunk_index})</h3>
              <button className="modal-close-btn" onClick={() => setActiveSource(null)}>✕</button>
            </div>
            <div className="source-modal-body">
              <div className="source-score-badge">
                🎯 Relevance Score: {(activeSource.similarity_score * 100).toFixed(1)}%
              </div>
              <div className="source-modal-content">
                {activeSource.chunk_text}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
