// LoginPage.jsx — Passwordless OTP Authentication
// Developer: vijay_sathappan
//
// Step 1: Enter email  → click "Send Code" → OTP emailed
// Step 2: Enter 6-digit OTP → click "Verify" → JWT issued, logged in
// Auto-creates account on first login — no separate register needed.

import { useState, useRef, useEffect } from 'react';
import { sendOtp, verifyOtp } from '../api';

export default function LoginPage({ onLogin, addToast }) {
  // Which step we're on: 'email' | 'otp'
  const [step, setStep] = useState('email');

  // Form values
  const [email, setEmail]   = useState('');
  const [otp, setOtp]       = useState(['', '', '', '', '', '']); // 6 boxes
  const [loading, setLoading] = useState(false);

  // Countdown timer (5 min = 300s)
  const [countdown, setCountdown] = useState(0);
  const timerRef = useRef(null);

  // Auto-focus OTP boxes
  const otpRefs = useRef([]);

  // Start countdown after OTP is sent
  function startCountdown() {
    setCountdown(300);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) { clearInterval(timerRef.current); return 0; }
        return c - 1;
      });
    }, 1000);
  }

  // Format seconds as mm:ss
  function formatTime(s) {
    const m = Math.floor(s / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  }

  useEffect(() => () => clearInterval(timerRef.current), []);

  // ── Step 1: Send OTP ─────────────────────────────────────────
  async function handleSendOtp(e) {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!trimmed || !trimmed.includes('@')) {
      addToast('Please enter a valid email address.', 'error');
      return;
    }
    setLoading(true);
    try {
      await sendOtp(trimmed);
      setEmail(trimmed);
      setStep('otp');
      setOtp(['', '', '', '', '', '']);
      startCountdown();
      addToast(`✉️ Code sent to ${trimmed}`, 'success');
      // Focus first OTP box after render
      setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Failed to send code. Try again.', 'error');
    } finally {
      setLoading(false);
    }
  }

  // ── Step 2: Verify OTP ───────────────────────────────────────
  async function handleVerifyOtp(e) {
    e.preventDefault();
    const code = otp.join('');
    if (code.length < 6) {
      addToast('Please enter all 6 digits.', 'error');
      return;
    }
    setLoading(true);
    try {
      const data = await verifyOtp(email, code);
      addToast(
        data.is_new_user ? '🎉 Welcome to DocMind AI!' : `👋 Welcome back!`,
        'success'
      );
      onLogin(data.access_token);
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Invalid or expired code.', 'error');
      // Clear OTP boxes on wrong code
      setOtp(['', '', '', '', '', '']);
      setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } finally {
      setLoading(false);
    }
  }

  // ── OTP box keyboard handling ────────────────────────────────
  function handleOtpChange(idx, val) {
    // Only allow a single digit
    const digit = val.replace(/\D/g, '').slice(-1);
    const next = [...otp];
    next[idx] = digit;
    setOtp(next);
    // Auto-advance to next box
    if (digit && idx < 5) {
      otpRefs.current[idx + 1]?.focus();
    }
    // Auto-submit when all 6 are filled
    if (next.every(d => d !== '') && next.join('').length === 6) {
      // small delay so last digit renders first
      setTimeout(() => handleVerifyOtpDirect(next.join('')), 80);
    }
  }

  function handleOtpKeyDown(idx, e) {
    // Backspace: clear current and move back
    if (e.key === 'Backspace') {
      const next = [...otp];
      if (next[idx]) {
        next[idx] = '';
        setOtp(next);
      } else if (idx > 0) {
        otpRefs.current[idx - 1]?.focus();
        next[idx - 1] = '';
        setOtp(next);
      }
      e.preventDefault();
    }
    // Arrow keys
    if (e.key === 'ArrowLeft' && idx > 0)  otpRefs.current[idx - 1]?.focus();
    if (e.key === 'ArrowRight' && idx < 5) otpRefs.current[idx + 1]?.focus();
  }

  function handleOtpPaste(e) {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(''));
      otpRefs.current[5]?.focus();
      e.preventDefault();
      setTimeout(() => handleVerifyOtpDirect(pasted), 80);
    }
  }

  // Direct verify (used when auto-submitting from paste / last digit)
  async function handleVerifyOtpDirect(code) {
    if (loading) return;
    setLoading(true);
    try {
      const data = await verifyOtp(email, code);
      addToast(data.is_new_user ? '🎉 Welcome to DocMind AI!' : '👋 Welcome back!', 'success');
      onLogin(data.access_token);
    } catch (err) {
      addToast(err?.response?.data?.detail || 'Invalid or expired code.', 'error');
      setOtp(['', '', '', '', '', '']);
      setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } finally {
      setLoading(false);
    }
  }

  // Resend OTP
  async function handleResend() {
    if (countdown > 0) return;
    setLoading(true);
    try {
      await sendOtp(email);
      setOtp(['', '', '', '', '', '']);
      startCountdown();
      addToast('New code sent!', 'success');
      setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } catch {
      addToast('Failed to resend. Try again.', 'error');
    } finally {
      setLoading(false);
    }
  }

  // ── Render ───────────────────────────────────────────────────
  return (
    <div className="login-page">
      <div className="login-bg-orb login-bg-orb-1" />
      <div className="login-bg-orb login-bg-orb-2" />

      <div className="login-card">
        {/* ── Header ── */}
        <div className="login-header">
          <div className="login-logo">🧠</div>
          <h1>DocMind AI</h1>
          <p>Intelligent Document Q&amp;A</p>
          <div className="dev-credit">by vijay_sathappan</div>
        </div>

        {/* ────────────── STEP 1 — Email Entry ────────────── */}
        {step === 'email' && (
          <form onSubmit={handleSendOtp}>
            <div className="otp-step-label">
              <span className="otp-step-icon">✉️</span>
              Enter your email to receive a login code
            </div>

            <div className="form-group" style={{ marginTop: '20px' }}>
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                autoFocus
                required
              />
            </div>

            <div className="form-actions">
              <button
                id="btn-send-otp"
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? <><span className="spinner" /> Sending code…</> : '📨 Send Login Code'}
              </button>
            </div>

            <div className="otp-note">
              🔒 No password needed. We&apos;ll email you a 6-digit code.
            </div>
          </form>
        )}

        {/* ────────────── STEP 2 — OTP Entry ────────────── */}
        {step === 'otp' && (
          <form onSubmit={handleVerifyOtp}>
            <div className="otp-step-label">
              <span className="otp-step-icon">🔢</span>
              Check your inbox at <strong>{email}</strong>
            </div>

            {/* 6-digit OTP input */}
            <div className="otp-boxes-wrap" onPaste={handleOtpPaste}>
              {otp.map((digit, idx) => (
                <input
                  key={idx}
                  id={`otp-${idx}`}
                  ref={(el) => (otpRefs.current[idx] = el)}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  className={`otp-box${digit ? ' filled' : ''}`}
                  value={digit}
                  onChange={(e) => handleOtpChange(idx, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                  autoComplete="one-time-code"
                  disabled={loading}
                />
              ))}
            </div>

            {/* Countdown */}
            <div className="otp-timer">
              {countdown > 0
                ? <><span className="otp-timer-dot" />Code expires in {formatTime(countdown)}</>
                : <span style={{ color: 'var(--danger)' }}>⏰ Code expired</span>}
            </div>

            <div className="form-actions">
              <button
                id="btn-verify-otp"
                type="submit"
                className="btn btn-primary"
                disabled={loading || otp.join('').length < 6}
              >
                {loading ? <><span className="spinner" /> Verifying…</> : '✅ Verify & Login'}
              </button>

              <button
                id="btn-change-email"
                type="button"
                className="btn btn-secondary"
                onClick={() => { setStep('email'); setOtp(['', '', '', '', '', '']); clearInterval(timerRef.current); }}
                disabled={loading}
              >
                ← Change Email
              </button>
            </div>

            {/* Resend */}
            <div className="otp-resend">
              Didn&apos;t receive it?{' '}
              <button
                id="btn-resend-otp"
                type="button"
                className="otp-resend-btn"
                onClick={handleResend}
                disabled={countdown > 0 || loading}
              >
                {countdown > 0 ? `Resend in ${formatTime(countdown)}` : 'Resend Code'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
