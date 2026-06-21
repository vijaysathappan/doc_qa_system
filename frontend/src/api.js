// api.js — All API calls to the FastAPI backend
// Developer: vijay_sathappan

import axios from 'axios';

// Dynamic API URL for Vercel serverless monorepo deployment
const API_URL = import.meta.env.VITE_API_URL || window.location.origin;

// Create a shared axios instance
const api = axios.create({ baseURL: API_URL });

// ── Auth ──────────────────────────────────────────────────────────────────────

/**
 * POST /auth/login
 * Uses OAuth2PasswordRequestForm format (form-encoded, not JSON)
 */
export async function login(email, password) {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  const res = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return res.data; // { access_token, token_type }
}

/**
 * POST /auth/register
 */
export async function register(email, password) {
  const res = await api.post('/auth/register', { email, password });
  return res.data;
}

// ── OTP (Passwordless) Auth ───────────────────────────────────────────────────

/**
 * POST /auth/send-otp  { email }
 * Generates a 6-digit OTP, stores in Redis (5 min), sends to email.
 * Returns { message, email, expires_in }
 */
export async function sendOtp(email) {
  const res = await api.post('/auth/send-otp', { email });
  return res.data;
}

/**
 * POST /auth/verify-otp  { email, otp }
 * Validates OTP. Auto-creates user if first login.
 * Returns { access_token, token_type, email, is_new_user }
 */
export async function verifyOtp(email, otp) {
  const res = await api.post('/auth/verify-otp', { email, otp });
  return res.data;
}

// ── Upload ────────────────────────────────────────────────────────────────────

/**
 * POST /upload/pdf
 * Sends the PDF file as multipart/form-data
 * Returns { document_id, chunks_created, filename, message }
 */
export async function uploadPdf(token, file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/upload/pdf', formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

// ── Query ─────────────────────────────────────────────────────────────────────

/**
 * POST /query/
 * Returns { question, answer, document_id, sources_used, from_cache }
 */
export async function queryDocument(token, documentId, question) {
  const res = await api.post(
    '/query/',
    { document_id: documentId, question },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data;
}

/**
 * GET /auth/me
 * Retrieves current user profile (including total tokens consumed)
 */
export async function getMe(token) {
  const res = await api.get('/auth/me', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function healthCheck() {
  const res = await api.get('/health');
  return res.data;
}
