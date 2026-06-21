# otp_auth.py — Passwordless OTP-via-email authentication
# Developer: vijay_sathappan
#
# Redis-optional: falls back to in-memory store if Redis is not running.
# SMTP-optional:  prints OTP to console if SMTP_USER is not configured.
#
# Flow:
#   1. POST /auth/send-otp  { email } → generates 6-digit OTP, stores it, emails it
#   2. POST /auth/verify-otp { email, otp } → verifies OTP, auto-creates user, returns JWT

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth_utils import create_access_token
import random
import smtplib
import uuid
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth-otp"])
limiter = Limiter(key_func=get_remote_address)

# ── OTP config ────────────────────────────────────────────────
OTP_TTL        = 300          # 5 minutes in seconds
OTP_KEY_PREFIX = "otp:"

# ── SMTP config ───────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

# ── In-memory OTP fallback ────────────────────────────────────
# Used when Redis is not running. Format: { "otp:{email}": (otp_str, expires_at_unix) }
_otp_memory_store: dict = {}

def _memory_set(key: str, value: str, ttl: int):
    _otp_memory_store[key] = (value, time.time() + ttl)

def _memory_get(key: str):
    entry = _otp_memory_store.get(key)
    if not entry:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        _otp_memory_store.pop(key, None)  # expired
        return None
    return value

def _memory_delete(key: str):
    _otp_memory_store.pop(key, None)

# ── Redis helpers (with in-memory fallback) ───────────────────
def _try_redis():
    """Return redis_client if Redis is reachable, else None."""
    try:
        from app.cache import redis_client
        redis_client.ping()   # quick connectivity check
        return redis_client
    except Exception:
        return None

def _store_otp(email: str, otp: str):
    key = f"{OTP_KEY_PREFIX}{email}"
    r = _try_redis()
    if r:
        r.setex(key, OTP_TTL, otp)
    else:
        _memory_set(key, otp, OTP_TTL)

def _get_otp(email: str):
    key = f"{OTP_KEY_PREFIX}{email}"
    r = _try_redis()
    if r:
        return r.get(key)
    return _memory_get(key)

def _delete_otp(email: str):
    key = f"{OTP_KEY_PREFIX}{email}"
    r = _try_redis()
    if r:
        r.delete(key)
    else:
        _memory_delete(key)

# ── Helpers ───────────────────────────────────────────────────

def _generate_otp() -> str:
    return f"{random.SystemRandom().randint(100000, 999999)}"


def _send_email(to_email: str, otp: str):
    """Send OTP email via SMTP; prints to console if SMTP not configured."""
    if not SMTP_USER or not SMTP_PASS:
        # Dev mode — print OTP to server console
        print("\n" + "="*45)
        print(f"  DEV MODE OTP for {to_email}: {otp}")
        print("  (Set SMTP_USER + SMTP_PASS in .env to email)")
        print("="*45 + "\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "DocMind AI - Your Login Code"
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_email

    text = f"Your DocMind AI login code is: {otp}\n\nExpires in 5 minutes.\n\n- vijay_sathappan"
    html = f"""
    <html><body style="font-family:Inter,sans-serif;background:#0a0e1a;margin:0;padding:40px">
      <div style="max-width:440px;margin:0 auto;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:40px;color:#f1f5f9">
        <div style="text-align:center;margin-bottom:28px">
          <div style="width:56px;height:56px;background:linear-gradient(135deg,#6366f1,#a78bfa);border-radius:12px;display:inline-flex;align-items:center;justify-content:center;font-size:26px">&#x1F9E0;</div>
          <h1 style="font-size:1.4rem;font-weight:800;margin:14px 0 4px;color:#f1f5f9">DocMind AI</h1>
          <p style="color:#94a3b8;font-size:0.875rem;margin:0">Your login verification code</p>
        </div>
        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
          <div style="font-size:2.4rem;font-weight:800;letter-spacing:0.2em;color:#818cf8;font-family:monospace">{otp}</div>
          <div style="color:#64748b;font-size:0.78rem;margin-top:8px">Expires in 5 minutes</div>
        </div>
        <p style="color:#64748b;font-size:0.8rem;text-align:center">If you didn't request this, ignore this email.</p>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:20px 0">
        <p style="color:#475569;font-size:0.72rem;text-align:center">Developed by vijay_sathappan</p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
    except Exception as e:
        print(f"[SMTP ERROR] {e} — OTP for {to_email}: {otp}")


# ── Pydantic models ───────────────────────────────────────────

class SendOTPRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp:   str


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/send-otp")
@limiter.limit("5/minute")
async def send_otp(
    request: Request,
    req: SendOTPRequest,
    background_tasks: BackgroundTasks
):
    email = req.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="Please provide a valid email address")

    otp = _generate_otp()

    # Store OTP (Redis if available, in-memory otherwise)
    _store_otp(email, otp)

    # Send email in background (or print to console in dev mode)
    background_tasks.add_task(_send_email, email, otp)

    return {
        "message":    "OTP sent! Check your email (or server console in dev mode).",
        "email":      email,
        "expires_in": OTP_TTL
    }


@router.post("/verify-otp")
@limiter.limit("10/minute")
async def verify_otp(
    request: Request,
    req: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    email = req.email.lower().strip()
    otp   = req.otp.strip()

    stored_otp = _get_otp(email)

    if not stored_otp:
        raise HTTPException(
            status_code=401,
            detail="OTP expired or not found. Please request a new one."
        )

    if stored_otp != otp:
        raise HTTPException(status_code=401, detail="Incorrect OTP. Please try again.")

    # OTP valid — delete immediately (one-time use)
    _delete_otp(email)

    # Auto-create user if first login
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password="__otp_user__"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type":   "bearer",
        "email":        user.email,
        "is_new_user":  (user.hashed_password == "__otp_user__")
    }
