// ChatArea.jsx — Main chat interface
// Mirrors streamlit_app.py lines 94-133 (chat area, history, input, query)
// Developer: vijay_sathappan

import { useEffect, useRef, useState } from 'react';
import { queryDocument } from '../api';
import ChatMessage from './ChatMessage';

export default function ChatArea({ token, docInfo, chatHistory, setChatHistory, addToast, onQuerySuccess }) {
  // Input state — mirrors st.chat_input("Ask a question about your document...")
  const [question, setQuestion] = useState('');
  const [thinking, setThinking]  = useState(false); // mirrors st.spinner("Thinking...")

  // Auto-scroll ref — mirrors Streamlit's auto-scroll behaviour
  const bottomRef = useRef(null);

  // Scroll to bottom whenever history or thinking state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, thinking]);

  // ── Submit question ───────────────────────────────────────────
  // Mirrors streamlit_app.py lines 110-133
  async function handleSubmit() {
    const q = question.trim();
    if (!q || thinking) return;

    setQuestion('');
    setThinking(true);

    // Optimistically append user message — mirrors: with st.chat_message("user"): st.write(question)
    setChatHistory((prev) => [...prev, { role: 'user', text: q }]);

    try {
      // Mirrors: requests.post(f"{API_URL}/query/", headers=headers, json={...})
      const data = await queryDocument(token, docInfo.document_id, q);

      // Append assistant message — mirrors: with st.chat_message("assistant"): st.write(data["answer"])
      setChatHistory((prev) => [
        ...prev,
        {
          role:         'assistant',
          text:         data.answer,
          fromCache:    data.from_cache,   // mirrors: if data.get("from_cache"): st.caption("⚡ Served from cache")
          sourcesUsed:  data.sources_used,
          sources:      data.sources,       // new: details about the specific dynamic chunks used
        },
      ]);

      // Call profile update to sync tokens in sidebar
      if (onQuerySuccess) {
        onQuerySuccess(data.tokens_used, data.total_tokens_consumed);
      }
    } catch (err) {
      // Mirrors: st.error(f"Query failed: {response.text}")
      addToast(
        err?.response?.data?.detail || 'Query failed. Please try again.',
        'error'
      );
      // Remove the optimistic user message on error
      setChatHistory((prev) => prev.slice(0, -1));
    } finally {
      setThinking(false);
    }
  }

  // Send on Enter (but Shift+Enter for newline)
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="chat-area">
      {/* ── Header — mirrors: st.subheader(f"📄 {st.session_state.doc_name}") ── */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="doc-icon">📄</div>
          <div>
            <h2>{docInfo.doc_name}</h2>
            <span className="chunks-count-info">{docInfo.chunks_created} chunks indexed</span>
          </div>
        </div>
        <span className="chunks-badge">
          Ready
        </span>
      </div>

      {/* ── Messages ── */}
      {/* Mirrors: for entry in st.session_state.chat_history: st.chat_message(...) */}
      <div className="messages-list">
        <div className="chat-max-container">
          {chatHistory.length === 0 && !thinking && (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '80px', fontSize: '0.875rem' }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📄</div>
              <h3>Ask anything about <span style={{ color: 'var(--accent-light)' }}>{docInfo.doc_name}</span></h3>
              <p style={{ marginTop: '8px', color: 'var(--text-secondary)' }}>Get semantically verified responses with source references</p>
            </div>
          )}

          {chatHistory.map((msg, idx) => (
            <ChatMessage
              key={idx}
              role={msg.role}
              text={msg.text}
              fromCache={msg.fromCache}
              sourcesUsed={msg.sourcesUsed}
              sources={msg.sources}
            />
          ))}

          {/* Typing indicator — mirrors st.spinner("Thinking...") */}
          {thinking && (
            <div className="message assistant">
              <div className="message-avatar">🧠</div>
              <div className="message-body">
                <div className="typing-indicator">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Input Bar — mirrors: question = st.chat_input("Ask a question...") ── */}
      <div className="chat-input-bar">
        <div className="chat-max-container">
          <div className="chat-input-container">
            <textarea
              id="chat-input"
              placeholder={`Ask a question about ${docInfo.doc_name}...`}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={thinking}
            />
            <div className="chat-input-controls">
              <span className="model-badge">⚡ Llama 3.1 8B</span>
              <button
                id="btn-send"
                className="send-btn"
                onClick={handleSubmit}
                disabled={!question.trim() || thinking}
                title="Send query"
              >
                {thinking ? <span className="spinner" /> : '➤'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
