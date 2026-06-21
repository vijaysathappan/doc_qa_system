// WelcomeScreen.jsx — Landing screen shown when no document is loaded
// Mirrors streamlit_app.py lines 84-93 (Step 1 / Step 2 info cards)
// Developer: vijay_sathappan

export default function WelcomeScreen() {
  return (
    <div className="welcome-screen">
      {/* ── Hero ── */}
      <div className="welcome-hero">
        <div className="welcome-icon">🧠</div>
        <h1>DocMind AI</h1>
        <p>
          Upload a PDF and ask anything about it. Get instant, grounded answers
          powered by semantic search and Groq&apos;s Llama 3.1.
        </p>
      </div>

      {/* ── Steps grid — mirrors st.info Step 1 / Step 2 ── */}
      <div className="steps-grid">
        <div className="step-card">
          <div className="step-number">Step 1</div>
          <h3>📁 Upload Document</h3>
          <p>
            Use the sidebar to upload your PDF. DocMind will extract, chunk,
            and embed it automatically.
          </p>
        </div>

        <div className="step-card">
          <div className="step-number">Step 2</div>
          <h3>💬 Ask Questions</h3>
          <p>
            Click <strong>Initialize DocMind</strong> then type any question.
            Answers are grounded in your document content.
          </p>
        </div>

        <div className="step-card">
          <div className="step-number">Step 3</div>
          <h3>⚡ Instant Cache</h3>
          <p>
            Repeated questions are served from Redis cache instantly — no
            redundant LLM calls.
          </p>
        </div>

        <div className="step-card">
          <div className="step-number">Step 4</div>
          <h3>🔒 Secure Access</h3>
          <p>
            JWT-based auth ensures your documents and sessions are private.
          </p>
        </div>
      </div>
    </div>
  );
}
