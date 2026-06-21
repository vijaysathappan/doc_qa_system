// App.jsx — Root component with global state management
// Mirrors streamlit_app.py session_state (token, document_id, chat_history, doc_name)
// Developer: vijay_sathappan

import { useState, useCallback, useEffect } from 'react';
import LoginPage    from './components/LoginPage';
import Sidebar      from './components/Sidebar';
import ChatArea     from './components/ChatArea';
import WelcomeScreen from './components/WelcomeScreen';
import { getMe }    from './api';
import './index.css';

// ── Toast System ──────────────────────────────────────────────
// Mirrors Streamlit's st.success / st.error / st.info calls
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          {t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : 'ℹ️'} {t.message}
        </div>
      ))}
    </div>
  );
}

export default function App() {
  // ── Global state — mirrors st.session_state ───────────────────
  // st.session_state.token
  const [token, setToken]             = useState(() => sessionStorage.getItem('token') || null);
  // st.session_state.document_id / doc_name / chunks — merged into one object
  const [docInfo, setDocInfo]         = useState(null);
  // st.session_state.chat_history
  const [chatHistory, setChatHistory] = useState([]);
  // Total tokens consumed by the user
  const [totalTokens, setTotalTokens] = useState(0);
  // Toast notifications (replaces st.success / st.error)
  const [toasts, setToasts]           = useState([]);

  // ── Fetch user profile ─────────────────────────────────────────
  const fetchUserProfile = useCallback(async (authToken) => {
    if (!authToken) return;
    try {
      const data = await getMe(authToken);
      setTotalTokens(data.total_tokens_consumed || 0);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
    }
  }, []);

  useEffect(() => {
    if (token) {
      fetchUserProfile(token);
    }
  }, [token, fetchUserProfile]);

  // ── Toast helpers ─────────────────────────────────────────────
  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    // Auto-dismiss after 3.5s — Streamlit messages auto-dismiss similarly
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  }, []);

  // ── Auth handlers ─────────────────────────────────────────────
  // Mirrors: st.session_state.token = response.json()["access_token"]; st.rerun()
  function handleLogin(accessToken) {
    sessionStorage.setItem('token', accessToken);
    setToken(accessToken);
    fetchUserProfile(accessToken);
  }

  // Mirrors: st.session_state.token = None; st.session_state.document_id = None; ...
  function handleLogout() {
    sessionStorage.removeItem('token');
    setToken(null);
    setDocInfo(null);
    setChatHistory([]);
    setTotalTokens(0);
  }

  // ── Document handlers ─────────────────────────────────────────
  // Mirrors: st.session_state.document_id = data["document_id"]; st.session_state.doc_name = ...
  function handleDocReady(info) {
    setDocInfo(info);
    setChatHistory([]); // mirrors: st.session_state.chat_history = []
  }

  // Mirrors: st.button("🗑️ Clear Document & Reset") handler
  function handleClear() {
    setDocInfo(null);
    setChatHistory([]);
  }

  // ── Render ────────────────────────────────────────────────────
  return (
    <>
      {/* ── LOGIN GATE — mirrors: if not st.session_state.token: ── */}
      {!token ? (
        <LoginPage onLogin={handleLogin} addToast={addToast} />
      ) : (
        /* ── MAIN APP — mirrors: else: ── */
        <div className="app-layout">
          {/* ── SIDEBAR — mirrors: with st.sidebar: ── */}
          <Sidebar
            token={token}
            docInfo={docInfo}
            onDocReady={handleDocReady}
            onClear={handleClear}
            onLogout={handleLogout}
            addToast={addToast}
            totalTokens={totalTokens}
          />

          {/* ── MAIN CONTENT ── */}
          <div className="main-content">
            {/* Mirrors: if not st.session_state.document_id: (welcome) else: (chat) */}
            {!docInfo ? (
              <WelcomeScreen />
            ) : (
              <ChatArea
                token={token}
                docInfo={docInfo}
                chatHistory={chatHistory}
                setChatHistory={setChatHistory}
                addToast={addToast}
                onQuerySuccess={(tokensUsed, totalTokensConsumed) => {
                  setTotalTokens(totalTokensConsumed);
                }}
              />
            )}
          </div>
        </div>
      )}

      {/* ── Global Toast Notifications ── */}
      <ToastContainer toasts={toasts} />
    </>
  );
}
